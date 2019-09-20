#!/usr/bin/python
# coding: utf-8

from subprocess import Popen, PIPE
import logging 

log = logging.getLogger('elastica')

def listar_dispositivos_montados():
    '''
    Devuelve un diccionario de tipo 
        {punto_montaje: dispositivo}
    '''
    fichero = '/proc/mounts'
    archivo = []
    contenido = {}
    with open(fichero) as f:
       archivo = f.readlines()

    for linea in archivo:
        dispositivo = linea.split(' ')[0]
        montaje = linea.split(' ')[1]
        contenido[montaje] = dispositivo

    return contenido

def listar_directorios_previos(directorio):
    '''
    Dado un directorio, forma una lista de los directorios previos posibles
    '''
    componentes = [ x for x in directorio.split('/') if x != '' ]
    a = []
    b = '/'
    for x in componentes:
        b += x + '/'
        a.append(b)

    return a

def buscar_punto_montaje(directorio, dispositivos_montados):
    '''
    Dado directorio, lo seccionará en directorios posibles:
    Después de eso, buscará cada una de esas posibilidades entre los puntos de montaje del sistema
    '''
    montaje = None
    directorios_posibles = listar_directorios_previos(directorio)
    for directorio in directorios_posibles:
        if directorio in dispositivos_montados:
            montaje = directorio
            break

    punto_montaje = montaje if montaje is not None else '/'

    log.debug('{} se encuentra montado en {}'.format(directorio, punto_montaje))

    return punto_montaje

def calcular_porcentaje_libre(particion):
    '''
    Calcula el porcentaje libre de la partición dada
    '''
    comando = ['df', '--output=used,avail', particion]
    ejecucion = Popen(comando, stdout=PIPE, stderr=PIPE)
    salida, error = ejecucion.communicate()
    
    if error == '':
        usado, libre = salida.encode('utf-8').split('\n')[1].split(' ')
        return round((float(libre) / (float(usado) + float(libre))) * 100, 2)
    
        log.debug('Uso de espacio en disco:{} - espacio libre: {}'.format(usado, libre))
    
    log.error('El sistema ha reportado un error: {}'.format(error))
    return float(0)
