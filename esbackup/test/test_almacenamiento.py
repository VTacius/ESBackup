import unittest
import sys

import mock

class obtieneMontajeDirectorio(unittest.TestCase):
    
    directorio = '/var/lib/elasticsearch/'
    esquema_particion_basico = {'/': '/dev/xvda2', '/home': '/dev/xvda3'}
    esquema_particion_avanzado = {'/': '/dev/xvda2', '/home': '/dev/xvda3', '/var/': '/dev/xvdb1'}

    def test_montaje_por_defecto(self):
        from esbackup.esbackup import buscar_punto_montaje
        
        esquema_particion = {'/': '/dev/xvda2', '/home': '/dev/xvda3'}
        
        respuesta = buscar_punto_montaje('/var', esquema_particion)

        self.assertEqual(respuesta, '/')
    
    def test_montaje_avanzado(self):
        from esbackup.esbackup import buscar_punto_montaje
        
        esquema_particion = {'/': '/dev/xvda2', '/home': '/dev/xvda3', '/var': '/dev/xvdb1'}

        respuesta = buscar_punto_montaje('/var/lib/elasticsearch', esquema_particion)

        self.assertEqual(respuesta, '/var')


