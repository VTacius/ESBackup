#!/usr/bin/python3

from sys import exit

from math import ceil

from functools import reduce

from argparse import ArgumentParser

from esbackup.utilidades import configurar_log
from esbackup.utilidades import conversor_unidades 

from esbackup.almacenamiento import calcular_porcentaje_libre
from esbackup.almacenamiento import listar_dispositivos_montados

from esbackup.peticiones import mergear
from esbackup.peticiones import shrinkear
from esbackup.peticiones import borrar_indice
from esbackup.peticiones import listar_indices
from esbackup.peticiones import habilitar_escritura_nodo

from esbackup.esbackup import clasificar_indices
from esbackup.esbackup import buscar_punto_montaje
from esbackup.esbackup import seleccionar_indices_a_borrar
from esbackup.esbackup import espacio_usado_indices
from esbackup.esbackup import seleccionar_indices_a_respaldar

# Este es el que usaremos en testing
log = configurar_log(verbosidad=4)

def calcular_espacio_requerido(espacio_ultimos_indices, porcentaje_requerido, espacio_usado, espacio_libre):
    # El sistema necesita tener 10% de espacio disponible, o elasticsearch entra en modo de solo-escritura
    espacio_minimo_requerido = (espacio_usado + espacio_libre) * 0.10

    espacio_estimado_para_nuevos_indices = espacio_ultimos_indices * (1 + porcentaje_requerido)

    # ¿Cuál es el espacio requerido a liberar?
    espacio_requerido = ceil(espacio_minimo_requerido + espacio_estimado_para_nuevos_indices)
    if espacio_requerido >= espacio_libre:
        espacio_requerido -= espacio_libre
    else:
        log.debug("Suficiente espacio libre {} para suplir lo requerido {}".format(espacio_libre, espacio_requerido))
        espacio_requerido = 0
    
    return espacio_requerido

def main():
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
    ## I PARTE: Trabajamos para obtener el espacio disponible necesario para nuevos índices. 
    #
    
    # ¿En que partición se encuentra ubicada la instalación de elasticsearch?
    montajes = listar_dispositivos_montados()
    particion_de_montaje = buscar_punto_montaje('/var/lib/elasticsearch/', montajes)
    usado, libre = calcular_porcentaje_libre(particion_de_montaje)
   
    # Listamos los indíces y los clasificamos por sus nombres
    lista_indices_activos = listar_indices(args.endpoint, indice=args.patron, claves='index,store.size', orden='index')
    if len(lista_indices_activos) == 0:
        log.error('No se encontraron indices con el patron dado: {}. Adiós'.format(args.patron))
        exit(1)
    tabla_indices_activos = clasificar_indices(lista_indices_activos)
    
    # ¿Cuánto es la suma de los espacios promedios usado por los últimos 3 índices activos de cada tipo disponible?
    espacio_ultimos_indices_activos = espacio_usado_indices(tabla_indices_activos, 3)
    
    # ¿Cuánto espacio necesito liberar?
    espacio_requerido = calcular_espacio_requerido(espacio_ultimos_indices_activos, args.porcentaje_requerido, usado, libre)
    
    log.info('Espacio disponible: {}. Espacio requerido: {}'.format(conversor_unidades(libre), conversor_unidades(espacio_requerido)))
    
    # Seleccionamos los indices backup a borrar, a ver que onda
    lista_indices_backup = listar_indices(args.endpoint, indice='*-backup-*', claves='index,store.size', orden='index')
    tabla_indices_backup = clasificar_indices(lista_indices_backup)
    lista_indices_borrables = seleccionar_indices_a_borrar(args.minimo_indices_backup_requeridos, espacio_requerido, tabla_indices_backup)
   
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
    indices_a_backupear = seleccionar_indices_a_respaldar(2, tabla_indices_activos)
    
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

if __name__ == "__main__":
    main()
