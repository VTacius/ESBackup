import unittest
import sys

import mock

import os 
current_path = os.path.dirname(os.path.realpath(__file__))
package_path = '/'.join(current_path.split('/')[:-1])
sys.path.append(package_path)

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
  
    def test_montajes(self):
        from elastica.almacenamiento import listar_dispositivos_montados
        contenido = "proc /proc proc rw,relatime 0 0\ntmpfs /dev/shm tmpfs rw,nosuid,nodev 0 0\n/dev/xvda2 / ext4 rw,relatime,errors=remount-ro,data=ordered 0 0"

        read_fake = mock.mock_open(read_data=contenido)
        with mock.patch('__builtin__.open', read_fake) as m:
            respuesta = listar_dispositivos_montados()
        respuesta_esperada = {'/proc': 'proc', '/': '/dev/xvda2', '/dev/shm': 'tmpfs'} 
        self.assertDictEqual(respuesta, respuesta_esperada)

    @mock.patch('elastica.almacenamiento.Popen')
    def test_porcentaje_usado(self, mock_popen):
        from elastica.almacenamiento import calcular_porcentaje_libre

        salida = "  Usados     Disp\n"
        salida += "44714430 19159816"

        process = mock_popen.return_value
        process.communicate.return_value = (salida, '')
        respuesta = calcular_porcentaje_libre('/')
        self.assertEqual(respuesta, 30.0)


