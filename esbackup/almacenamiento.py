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

def calcular_porcentaje_libre(particion):
    '''
    Calcula el porcentaje libre de la partición dada
    '''
    comando = ['df', '--output=used,avail', particion]
    ejecucion = Popen(comando, stdout=PIPE, stderr=PIPE)
    salida, error = ejecucion.communicate()
   
    if error.decode() == '':
        usado, libre = salida.decode('utf-8').split('\n')[1].split(' ')
    
        log.debug('Uso de espacio en disco:{} - espacio libre: {}'.format(usado, libre))

        return float(usado), float(libre)
    
    log.error('El sistema ha reportado un error: {}'.format(error))
    return float(0)
