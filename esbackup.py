#!/usr/bin/python3

from sys import exit

from math import ceil

from functools import reduce

from argparse import ArgumentParser

from elastica.utilidades import configurar_log
from elastica.utilidades import conversor_unidades 

from elastica.almacenamiento import calcular_porcentaje_libre
from elastica.almacenamiento import buscar_punto_montaje
from elastica.almacenamiento import listar_dispositivos_montados

from elastica.peticiones import mergear
from elastica.peticiones import shrinkear
from elastica.peticiones import borrar_indice
from elastica.peticiones import listar_indices
from elastica.peticiones import habilitar_escritura_nodo

# Este es el que usaremos en testing
log = configurar_log(verbosidad=4)

def separador(linea):
    iname, tamanio = linea.split()
    clave = iname.split('-')[0]
    
    return clave, iname, int(tamanio)


def clasificar_indices(tabla):
    indices = {}
    for linea in tabla:
        clave, iname, tamanio = separador(linea)
        elemento = (iname, tamanio)
        if clave in indices:
            indices[clave].append(elemento)
        else:
            indices[clave] = [elemento]

    return indices


def seleccionar_indices_a_borrar(minimo_indices_requerido, espacio_libre_requerido, espacio_libre_sistema, indices):
    libre = espacio_libre_sistema
    indices_a_borrar= []
    
    while espacio_libre_requerido > libre:
        ultimos_indices = [y[0][0] for x, y in indices.items() if len(y) > minimo_indices_requerido]

        if len(ultimos_indices) == 0:
            break
       
        indices_a_borrar += ultimos_indices
        espacio_borrado = sum([y[0][1] for x, y in indices.items() if len(y) > minimo_indices_requerido])

        # Quitamos los índices borrados de las listas correspondientes
        indices = {x: y[1:] for x,y in indices.items()}
        
        ## ¿Cuánto espacio disponible tenemos ahora?
        libre += espacio_borrado 
   
    log.info("Seleccionados {} indices a borrar, habrá {} de espacio libre en el sistema".format(len(indices_a_borrar), conversor_unidades(libre)))
    log.debug(indices_a_borrar)
    
    return indices_a_borrar

if __name__ == "__main__":
    parser = ArgumentParser(description="Backup para indices de ElasticSearch")
    parser.add_argument('--verbose', '-v', default=2, action='count')
    parser.add_argument('--salida', '-s', default='console', choices=['console', 'syslog'])
    parser.add_argument('--patron', '-p', default='*-activo-*')
    parser.add_argument('--porcentaje-requerido', '-r', default=0.5, type=float)
    parser.add_argument('--endpoint', '-u', default='http://127.0.0.1:9200')
    parser.add_argument('--minimo-indices-backup-requeridos', '-b', default=2, type=int)
    parser.add_argument('--minimo-indices-activo-requeridos', '-a', default=2, type=int)
    parser.add_argument('--mergear', '-m', action='store_true')
    max_num_segments = 1
    
    args = parser.parse_args()
    
    log = configurar_log(args.salida, args.verbose)
    log.debug(args)

    log.warning('Empiezan las operaciones')
    log.warning('Fase I: Disponemos el servidor para operaciones')
    
    ### TODO: Falta algo bien importante. Si el servidor tiene menos de 10%, no dejara hacer nada de esto

    ###
    ## I PARTE: Trabajamos el espacio disponible. Es prácticamente la parte más complicada de todo esto
    #
    
    # ¿En que partición se encuentra ubicada la instalación de elasticsearch?
    montajes = listar_dispositivos_montados()
    particion_de_montaje = buscar_punto_montaje('/var/lib/elasticsearch/', montajes)
    usado, libre = calcular_porcentaje_libre(particion_de_montaje)
    
    # El sistema necesita tener 10% de espacio disponible, o elasticsearch entra en modo de solo-escritura
    espacio_total = usado + libre
    espacio_minimo_requerido = espacio_total * 0.10
    
    # Listamos los indíces y los clasificamos por sus nombres
    lista_indices_activos = listar_indices(args.endpoint, indice=args.patron, claves='index,store.size', orden='index')
    if len(lista_indices_activos) == 0:
        log.error('No se encontraron indices con el patron dado: {}. Adiós'.format(args.patron))
        exit(1)
    tabla_indices_activos = clasificar_indices(lista_indices_activos)
   
    # ¿Cuánto es el espacio usado por los últimos 3 índices activos
    promedio_tamanio = lambda lista: sum([x[1] for x in lista]) / len(lista)
    gspacio_ultimos_indices_activos = ceil(sum([promedio_tamanio(y[:3]) for x, y in tabla_indices_activos.items()])) 
    
    # ¿Cuál es el espacio requerido 
    espacio_requerido = ceil((espacio_ultimos_indices_activos * args.porcentaje_requerido) + espacio_minimo_requerido) 
    
    log.info('Espacio disponible: {}. Espacio requerido: {}'.format(conversor_unidades(libre), conversor_unidades(espacio_requerido)))
    log.debug('{} de uso promedio para los índices'.format(conversor_unidades(espacio_ultimos_indices_activos)))
    log.debug('{} el 11% de espacio requerido como libre en disco por parte de elasticsearch'.format(conversor_unidades(espacio_minimo_requerido)))
    
    # Seleccionamos los indices backup a borrar, a ver que onda
    lista_indices_backup = listar_indices(args.endpoint, indice='*-backup-*', claves='index,store.size', orden='index')
    tabla_indices_backup = clasificar_indices(lista_indices_backup)
    lista_indices_borrables = seleccionar_indices_a_borrar(args.minimo_indices_backup_requeridos, espacio_requerido, libre, tabla_indices_backup)
    
    # Borramos los índices y guardamos los resultados
    resultado = [borrar_indice(args.endpoint, indice) for indice in lista_indices_borrables]
    errores = [indice for indice in resultado if not indice['acknowledged']]
    
    # ¿Sucedió algún error al borrar índices?
    if len(errores) > 0:
        log.error('Algunos indices tuvieron problemas para borrarse')
        log.debug(errores)
    
    # Si es que aún no hay espacio suficiente, borramos algunos activos hasta un número de activos requeridos
    usado, libre = calcular_porcentaje_libre(particion_de_montaje) 
    if espacio_requerido > libre:
        lista_indices_borrables = seleccionar_indices_a_borrar(args.minimo_indices_activo_requeridos, espacio_requerido, libre, tabla_indices_activos)
        
        # Borramos los índices y guardamos los resultados
        resultado = [borrar_indice(args.endpoint, indice) for indice in lista_indices_borrables]
        errores = [indice for indice in resultado if not indice['acknowledged']]
        
        # ¿Sucedió algún error al borrar índices?
        if len(errores) > 0:
            log.error('Algunos indices tuvieron problemas para borrarse')
            log.debug(errores)
        
    # Si aún sigue sin haber espacio, nada, te mueres 
    usado, libre = calcular_porcentaje_libre(particion_de_montaje) 
    if espacio_requerido > libre:
        log.critical('No hay espacio disponible después de haber borrado todos los índices permisibles; es imposible continuar sin intervención por parte del usuario')
        exit(1)
    
    ###
    ## II PARTE: Habilitamos el servidor para las operaciones
    #
    log.info('Habilitamos el nodo para operaciones')
    habilitar_escritura_nodo(args.endpoint)
    
    ###
    ## III PARTE: Buscamos los índices sobre los cuales vamos a trabajar 
    #
    indices_a_backupear = reduce(lambda resultado, actual: resultado + actual[1][:-args.minimo_indices_activo_requeridos], tabla_indices_activos.items(), [])
    
    ###
    ## IV PARTE: Operamos sobre los índices backupeables
    #
    for indice in indices_a_backupear:
        nombre_indice_backup = shrinkear(args.endpoint, indice)
        
        if not nombre_indice_backup:
            log.error("Pues que fallamos al shrinkear")
        
        respuesta_merge = False
        if args.mergear and nombre_indice_backup:
            log.info("Backup de {} en indice {}".format(indice, nombre_indice_backup))
            respuesta_merge = mergear(args.endpoint, nombre_indice_backup, max_num_segments)
        
        if args.mergear and not respuesta_merge:
            log.error("Pues que fallamos al mergear")
        
        if nombre_indice_backup: 
            borrar_indice(args.endpoint, indice)

