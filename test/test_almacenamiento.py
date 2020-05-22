import unittest
import sys

import mock

class obtieneMontajeDirectorio(unittest.TestCase):
    
    directorio = '/var/lib/elasticsearch/'
    esquema_particion_basico = {'/': '/dev/xvda2', '/home': '/dev/xvda3'}
    esquema_particion_avanzado = {'/': '/dev/xvda2', '/home': '/dev/xvda3', '/var/': '/dev/xvdb1'}

    def test_montaje_por_defecto(self):
        from elastica.almacenamiento import buscar_punto_montaje
        respuesta = buscar_punto_montaje(self.directorio, self.esquema_particion_basico)

        self.assertEqual(respuesta, '/')
    
    def test_montaje_avanzado(self):
        from elastica.almacenamiento import buscar_punto_montaje
        respuesta = buscar_punto_montaje(self.directorio, self.esquema_particion_avanzado)

        self.assertEqual(respuesta, '/var/')

    def test_directorios_previos(self):
        from elastica.almacenamiento import listar_directorios_previos
        respuesta = listar_directorios_previos('/usr/local/etc/hostapd')

        self.assertListEqual(respuesta, ['/usr/', '/usr/local/', '/usr/local/etc/', '/usr/local/etc/hostapd/'])


class obtieneMontajesSistema(unittest.TestCase):
    #@mock.patch('builtins.open', new_callable_mock_open, read_data=contenido)
    def test_montajes(self):
        from elastica.almacenamiento import listar_dispositivos_montados
        contenido = "proc /proc proc rw,relatime 0 0\ntmpfs /dev/shm tmpfs rw,nosuid,nodev 0 0\n/dev/xvda2 / ext4 rw,relatime,errors=remount-ro,data=ordered 0 0"
        respuesta_esperada = {'/proc': 'proc', '/': '/dev/xvda2', '/dev/shm': 'tmpfs'} 

        read_fake = mock.mock_open(read_data=contenido)
        with mock.patch('builtins.open', read_fake) as m:
            respuesta = listar_dispositivos_montados()
        self.assertDictEqual(respuesta, respuesta_esperada)


