#!/usr/bin/python
"""Algunas utilidades base a usar en los demás módulos"""

import logging

from sys import stdout
from logging.handlers import SysLogHandler


def conversor_unidades(kilobytes):
    """Dado un valor en kilobytes, convierte a una frase humanamente legible"""
    sufijos = ['KB', 'MB', 'GB', 'TB']
    valor = counter = 0
    while kilobytes > 1:
        counter += 1
        valor, kilobytes = kilobytes, kilobytes / 1024

    sufijo = sufijos[counter - 1 if counter > 0 else 0]

    return "{:.2f}{}".format(valor, sufijo)


def configurar_log(salida='console', verbosidad=0):
    """Configura el log"""
    log = logging.getLogger(__name__)
    verbosidad = 4 if verbosidad > 4 else verbosidad
    nivel = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'][verbosidad]
    formato = logging.Formatter('elastica[%(process)s] %(module)s.%(funcName)s: %(message)s')

    handler = None
    if salida == 'syslog':
        handler = SysLogHandler(address='/dev/log')
    else:
        handler = logging.StreamHandler(stdout)

    nivel_verbosidad = getattr(logging, nivel)
    handler.setLevel(nivel_verbosidad)
    handler.setFormatter(formato)

    log = logging.getLogger('elastica')

    log.setLevel(nivel_verbosidad)
    if not log.handlers:
        log.addHandler(handler)
    else:
        manejador = log.handlers[0]
        log.removeHandler(manejador)
        log.addHandler(handler)

    return log
