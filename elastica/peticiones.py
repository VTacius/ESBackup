#!/usr/bin/python
# coding: utf-8

import requests
import logging 

log = logging.getLogger('elastica')

endpoint = 'http://127.0.0.1:9200'
max_num_segments = 1

# DATOS: Con este convertis lo que necesitas un indice
datos_shrink = {
    'settings': {
        'index': {
            'number_of_replicas': 0,
            'number_of_shards': 1,
            'codec': 'best_compression'
            }
        }
    }

# DATOS: Con este volves de sólo lectura a un indice
datos_index_block_write = {
    'settings': {
        'index': {
            'blocks': {
                'write': True
                }
            }
        }
    }

datos_revierte_only_read = {
    'index': {
        'blocks': {
            'read_only': False,
            'read_only_allow_delete': False
        }
                      }
    }

def _peticionar(metodo, url, datos=None, respuesta_tipo='json'):
    metodo = requests.__getattribute__(metodo) 

    peticion = metodo(url) if datos is None else metodo(url, json=datos)
    
    respuesta = None
    if respuesta_tipo == 'json':
        respuesta = peticion.json() 
    else:
        respuesta = [''] if peticion.text == '' else [x for x in peticion.text.split('\n') if len(x)>0]
    
    if peticion.status_code == 200: 
        return respuesta
    else:
        mensaje = respuesta['error']['type'] + ': ' + respuesta['error']['reason']
        log.error(mensaje)
        return False

def listar_indices(endpoint, indice='*', orden=None):
    ordenamiento = '?h=index,pri,store.size,health,status'
    ordenamiento += '&s=' + orden if orden is not None else ""
    url = '{endpoint}/_cat/indices/{indice}/{ordenamiento}'.format
    url = url(endpoint=endpoint, indice=indice, ordenamiento=ordenamiento)
    
    contenido = _peticionar('get', url, respuesta_tipo = 'texto')
    
    return contenido

def habilitar_escritura_nodo(endpoint):
    """
    Usa datos_revierte_only_read para que todo el clúster sea capaz de escribir
    """
    url = "{endpoint}/_all/_settings".format
    url = url(endpoint=endpoint)
    retorno = _peticionar('put', url, datos=datos_revierte_only_read)

def shrinkear(endpoint, indice):
    log.info('Shrinkea {}'.format(indice))
    
    # Primero, le volvemos de solo lectura
    log.debug('Shrinkea {}: Conversion a sólo lectura'.format(indice))
    url = "{endpoint}/{indice}/_settings".format
    url = url(endpoint=endpoint, indice=indice)
    retorno_lectura = _peticionar('put', url, datos_index_block_write)

    # Después le reducimos
    log.debug('Shrinkea {}: Operación shrink'.format(indice))
    url = "{endpoint}/{indice}/_shrink/{indice_backup}".format
    indice_backup = indice.replace('activo', 'backup')
    url = url(endpoint=endpoint, indice=indice, indice_backup=indice_backup)
    retorno_shrink = _peticionar('post', url, datos_shrink)

    if retorno_lectura and retorno_shrink:
        return indice_backup 
    else:
        return False

def mergear(endpoint, indice, max_num_segments):
    log.info('Merger {}'.format(indice))
    
    ## Antes de forzar el merge, volvemos de sólo lectura
    log.debug('Merger {}: Conversión a sólo lectura'.format(indice))
    url = "{endpoint}/{indice_backup}/_settings".format
    url = url(endpoint=endpoint, indice_backup=indice.replace('activo', 'backup'))
    retorno_lectura = _peticionar('put', url, datos=datos_index_block_write)

    # Forzamos el merge
    # TODO: Sólo debería ocurrir si hay al menos 2.5 veces el tamaño en espacio de disco disponible
    # TODO: Sólo debe ocurrir si existe
    log.debug('Merger {}: Operación merge'.format(indice))
    url = "{endpoint}/{indice_backup}/_forcemerge?max_num_segments={max_num_segments}".format
    url = url(endpoint=endpoint, indice_backup=indice.replace('activo', 'backup'), max_num_segments=max_num_segments)
    retorno_merge = _peticionar('post', url)

    return retorno_lectura and retorno_merge

def borrar_indice(endpoint, indice):
    log.info('Borrado {}'.format(indice))
    
    url = "{endpoint}/{indice}/".format
    url = url(endpoint=endpoint, indice=indice)
    retorno_borrado = _peticionar('delete', url)

    return retorno_borrado
