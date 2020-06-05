"""Prueba las funciones relacionadas con la búsqueda automatizada del punto de montaje"""
import unittest


class ObtieneMontajeDirectorio(unittest.TestCase):

    directorio = '/var/lib/elasticsearch/'
    esquema_particion_basico = {'/': '/dev/xvda2', '/home': '/dev/xvda3'}
    esquema_particion_avanzado = {'/': '/dev/xvda2', '/home': '/dev/xvda3', '/var/': '/dev/xvdb1'}

    def test_montaje_por_defecto(self):
        """¿Devuelve un valor por predeterminado '/' si es que no hay montaje especial"""
        from esbackup.esbackup import buscar_punto_montaje

        esquema_particion = {'/': '/dev/xvda2', '/home': '/dev/xvda3'}

        respuesta = buscar_punto_montaje('/var', esquema_particion)

        self.assertEqual(respuesta, '/')

    def test_montaje_avanzado(self):
        """Encuentra correctamente el punto de montaje personalizado para nuestra instalación"""
        from esbackup.esbackup import buscar_punto_montaje

        esquema_particion = {'/': '/dev/xvda2', '/home': '/dev/xvda3', '/var': '/dev/xvdb1'}

        respuesta = buscar_punto_montaje('/var/lib/elasticsearch', esquema_particion)

        self.assertEqual(respuesta, '/var')
