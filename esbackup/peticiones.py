#!/usr/bin/python
"""Implementando requests para nuestras necesidades especifícas"""

import logging
import requests

log = logging.getLogger('elastica')

# DATOS: Con este convertis lo que necesitas un indice
DATOS_SHRINK = {'settings': {
    'index': {
        'number_of_replicas': 0,
        'number_of_shards': 1,
        'codec': 'best_compression'}}}

# DATOS: Con este volves de sólo lectura a un indice
DATOS_INDEX_BLOCK_WRITE = {'settings': {
    'index': {
        'blocks': {
            'write': True}}}}

DATOS_REVIERTE_ONLY_READ = {
    'index': {'blocks': {
        'read_only': False,
        'read_only_allow_delete': False}}}


def _peticionar(metodo, url, datos=None, respuesta_tipo='json'):
    """La estructura base para todas las demás peticiones"""
    verbo = requests.__getattribute__(metodo)

    log.info('Peticionando: {} {}'.format(metodo.upper(), url))
    peticion = verbo(url) if datos is None else verbo(url, json=datos)

    respuesta = None
    if respuesta_tipo == 'json':
        respuesta = peticion.json()
    else:
        respuesta = [''] if peticion.text == '' else [x for x in peticion.text.split('\n') if len(x) > 0]

    if peticion.status_code == 200:
        return respuesta
    else:
        error = peticion.json()
        mensaje = error['error']['type'] + ': ' + error['error']['reason']
        log.error("Peticionando: Error {}".format(mensaje))
        return {'acknowledged': False, 'error': mensaje}


def listar_indices(endpoint, indice='*', claves='index,pri,store.size,health,status', orden=None):
    """Obtiene una lista de índices según los atributos dados"""
    query = '?bytes=k&h=' + claves
    query += '&s=' + orden if orden is not None else ""
    url = '{endpoint}/_cat/indices/{indice}/{query}'.format
    url = url(endpoint=endpoint, indice=indice, query=query)

    respuesta = _peticionar('get', url, respuesta_tipo='texto')
    if 'acknowledged' in respuesta and not respuesta['acknowledged']:
        return []
    else:
        return respuesta


def habilitar_escritura_nodo(endpoint):
    """ Usa DATOS_REVIERTE_ONLY_READ para que todo el clúster sea capaz de escribir """
    url = "{endpoint}/_all/_settings".format
    url = url(endpoint=endpoint)

    return _peticionar('put', url, datos=DATOS_REVIERTE_ONLY_READ)


def shrinkear(endpoint, indice):
    """ Ejecutamos el backup de un índice activo """
    log.info('Shrinkea {}'.format(indice))

    # Primero, le volvemos de solo lectura
    log.debug('Shrinkea {}: Conversion a sólo lectura'.format(indice))
    url = "{endpoint}/{indice}/_settings".format(endpoint=endpoint, indice=indice)
    respuesta = _peticionar('put', url, DATOS_INDEX_BLOCK_WRITE)

    # Después le reducimos
    if 'acknowledged' in respuesta and respuesta['acknowledged']:
        log.debug('Shrinkea {}: Operación shrink'.format(indice))
        indice_backup = indice.replace('activo', 'backup')
        url = "{endpoint}/{indice}/_shrink/{indice_backup}".format(endpoint=endpoint, indice=indice, indice_backup=indice_backup)
        respuesta = _peticionar('post', url, DATOS_SHRINK)
        if 'acknowledged' in respuesta and respuesta['acknowledged']:
            return indice_backup
        else:
            log.error("Shrinkea: Esto es el error de parte del servidor {}".format(respuesta))
            return False
    else:
        log.error("Shrinkea: Esto es el error de parte del servidor {}".format(respuesta))
        return False


def mergear(endpoint, indice, max_num_segments):
    """ Reduce los segmentos de un indíce backup """
    log.info('Merger {}'.format(indice))

    indice_backup = indice.replace('activo', 'backup')
    ## Antes de forzar el merge, volvemos de sólo lectura
    log.debug('Merger {}: Conversión a sólo lectura'.format(indice))
    url = "{endpoint}/{indice}/_settings".format(endpoint=endpoint, indice=indice_backup)
    respuesta = _peticionar('put', url, datos=DATOS_INDEX_BLOCK_WRITE)

    if 'acknowledged' in respuesta and respuesta['acknowledged']:
        # Forzamos el merge
        log.debug('Merger {}: Operación merge'.format(indice))
        url = "{endpoint}/{indice_backup}/_forcemerge?max_num_segments={max_num_segments}".format(endpoint=endpoint, indice_backup=indice.replace('activo', 'backup'), max_num_segments=max_num_segments)
        respuesta = _peticionar('post', url)
        if '_shards' in respuesta and 'successful' in respuesta['_shards']:
            return True
        else:
            log.error("Shrinkea: Esto es el error de parte del servidor {}".format(respuesta))
            return False
    else:
        log.error("Merger: Esto es el error de parte del servidor {}".format(respuesta))
        return False


def borrar_indice(endpoint, indice):
    """ Borra un índice """
    log.info('Borrado {}'.format(indice))

    url = "{endpoint}/{indice}/".format
    url = url(endpoint=endpoint, indice=indice)
    retorno_borrado = _peticionar('delete', url)

    return retorno_borrado
