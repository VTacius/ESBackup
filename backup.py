#!/usr/bin/python
# coding: utf-8

from elastica.peticiones import shrinkear
from elastica.peticiones import mergear
from elastica.peticiones import borrar_indice

from elastica.peticiones import listar_indices
from elastica.peticiones import habilitar_escritura_nodo

from elastica.almacenamiento import buscar_punto_montaje
from elastica.almacenamiento import calcular_porcentaje_libre
from elastica.almacenamiento import listar_dispositivos_montados

import re
from sys import exit, stdout
from time import sleep
import argparse
import logging
from datetime import date

fecha_hoy = date.today() 
endpoint = 'http://127.0.0.1:9200'
dias_pasados = 3
max_num_segments = 1
porcentaje_disco_minimo_requerido = 28
limite_intentos_borrar_indices = 10

# TODO: Posiblemente haya que cambiar gran parte de todo esto, básicamente si queremos que el mensaje de backup sea más realista
# Por ahora, resulta que nunca da el tamaño verdadero del index backup

def configurar_log(salida='console', verbosidad=0):
    verbosidad = verbosidad if verbosidad <= 3 else 3
    nivel = ['CRITICAL', 'ERROR', 'INFO', 'DEBUG'][verbosidad]
    formato = logging.Formatter('%(module)s.%(funcName)s: %(message)s')

    handler = None
    if salida == 'syslog':
        handler = logging.handlers.SysLogHandler(address = '/dev/log')
    else:
        handler = logging.StreamHandler(stdout)

    nivel_verbosidad = getattr(logging, nivel)
    handler.setLevel(nivel_verbosidad)
    handler.setFormatter(formato)

    log = logging.getLogger('elastica')
    log.setLevel(nivel_verbosidad)
    log.addHandler(handler)

    return log

def obtiene_info_indice(linea):
    contenido = linea.split()
    if len(contenido) > 0:
        nombre, shards, tamanio, salud, disponibilidad = contenido
        tipo, estado, fecha = contenido[0].split('-')
        return (nombre, fecha, tamanio, int(shards), estado, salud, disponibilidad)
    else:
        return (None, None, None, None, None, None, None)

def verifica_antiguedad(dias_anteriores, fecha_hoy, fecha_indice):
    fecha_indice = date(*[int(x) for x in fecha_indice.split('.')])

    delta = abs(fecha_hoy - fecha_indice)

    return delta.days > dias_anteriores


def disponer_nodo_para_operaciones():
    """
    Borra los indices de tipo *backup* hasta que haya espacio suficiente para hacer las operaciones
    De hecho, es posible que siga habiendo otros indices que no haya borrado, por ahora, me limito a
      borrar los de tipo backup
    """
    print('Empieza las joyas de la corona')
    montajes = listar_dispositivos_montados()
    punto_montaje = buscar_punto_montaje('/var/lib/elasticsearch/', montajes)
    libre = calcular_porcentaje_libre(punto_montaje)
   
    intentos_realizados = 1
    while libre < porcentaje_disco_minimo_requerido:
        indices = listar_indices(endpoint, '*backup*', 'store.size:desc,index:asc')
       
        # Es posible que no le devuelva indices 
        if len(indices) == 0 or indices[0] == "":
            break

        # Por si el disco esta lleno por una razón ajena a los indices de elasticsearch, evitamos así un loop
        if intentos_realizados >= limite_intentos_borrar_indices:
            break

        nombre_indice = indices[0].split()[0]
        borrar_indice(endpoint, nombre_indice)
       
        intentos_realizados += 1
        libre = calcular_porcentaje_libre(punto_montaje)
    else:
        habilitar_escritura_nodo(endpoint)
        return True
    
    return False

def verificar_existencia_indice(indice):
    """
    La expresión regular define el nombre completo de TODOS los índices propios
    Ayuda a argparser a analizar que el indice/patrón existe, y aprovechando, pues le tira
    el resultado 
    """
    regex = re.compile(r"^\w+\-activo-(?:\d){4}\.(?:(?:\d){2}\.?){2}$")
    indice = indice if regex.match(indice) else indice + '*'
    indices = listar_indices(endpoint, indice, 'index:asc') 
   
    if len(indices) == 0 or indices[0] == "":
        mensaje = "No se encuentran indices con el nombre/patrón de " + indice
        raise argparse.ArgumentTypeError(mensaje)

    return indices

def backupear_indice(nombre_indice_activo, fecha_indice_activo, debe_mergearse=True):
    """
    Ejecuta precisamente las operaciones de backup
    nombre_indice_activo no se valida porque ya lo estuvo
    """
    # TODO: Tení que trabajar en los cientos de verificaciones que quieres hacer

    if verifica_antiguedad(dias_pasados, fecha_hoy, fecha_indice_activo):
        nombre_indice_backup = shrinkear(endpoint, nombre_indice_activo)
        if debe_mergearse:
            mergear(endpoint, nombre_indice_backup, max_num_segments)
        borrar_indice(endpoint, nombre_indice_activo)
        contenido = verificar_existencia_indice(nombre_indice_backup)
        return contenido[0]
    
    return False

def operacion_principal(contenido_indice_activo):
    nombre_indice_activo, fecha_activo, tamanio_activo, shards_activo, estado_activo, salud_activo, disponibilidad_activo = obtiene_info_indice(contenido_indice_activo)
    contenido_indice_backup = backupear_indice(nombre_indice_activo, fecha_activo)
    
    if contenido_indice_backup is not False:
        nombre_indice_backup, fecha_backup, tamanio_backup, shards_backup, estado_backup, salud_backup, disponibilidad_backup = obtiene_info_indice(contenido_indice_backup)
        mensaje = "Indice: {} de {} con {} shards ha sido backupeado en {} de {} con {} shards".format
        mensaje = mensaje(nombre_indice_activo, tamanio_activo, shards_activo, nombre_indice_backup, tamanio_backup, shards_backup)
        log.info(mensaje)
    else:
        log.info("Indice: {} no se ha backupeado".format(nombre_indice_activo))

if __name__ == '__main__':
    ## No pude contenerme a que quedara bien bonito con argparser
    parser = argparse.ArgumentParser(description="Backup para indices de ElasticSearch")
    parser.add_argument('--verbose', '-v', action='count', default=0,
            help='Este es un argumento sobre el ser y la nada')
    parser.add_argument('--salida', '-s', default='console', choices=['console', 'syslog'],
            help='Salida de la información del script')
    
    grupos = parser.add_mutually_exclusive_group(required=True)
    grupos.add_argument('--indice', '-i', type=verificar_existencia_indice,
            help='Especifica un index sobre el cual hacer un backup')
    grupos.add_argument('--patron-indice', '-p', type=verificar_existencia_indice,
            help='Especifica un patron de indice sobre los cuales hacer un backup')

    args = parser.parse_args()
    
    # Configuro el logging
    log = configurar_log(args.salida, args.verbose)
    
    ## Empiezan las operaciones.
    resultado = disponer_nodo_para_operaciones()
    
    if resultado is False:
        log.critical('Pues no puedo disponer del servidor')
        exit()
 
    # TODO: ¿Necesito unir backupear_indice y el resto de estas operaciones?
    if args.indice is not None:
        contenido_indice = args.indice[0]
        operacion_principal(contenido_indice)
    else:
        contenido_indice = args.patron_indice
        for index in contenido_indice:
            operacion_principal(index)

