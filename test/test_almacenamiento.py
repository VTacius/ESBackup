import unittest

class TestObtieneMontajeDirectorio(unittest.TestCase):
    
    def test_montaje_por_defecto(self):
        from elastica.rustilidades import buscar_punto_montaje
        
        esquema_particion = {'/': '/dev/xvda2', '/home': '/dev/xvda3'}
        
        respuesta = buscar_punto_montaje('/var', esquema_particion)

        self.assertEqual(respuesta, '/')
    
    def test_montaje_avanzado(self):
        from elastica.rustilidades import buscar_punto_montaje
        
        esquema_particion = {'/': '/dev/xvda2', '/home': '/dev/xvda3', '/var': '/dev/xvdb1'}

        respuesta = buscar_punto_montaje('/var/lib/elasticsearch', esquema_particion)

        self.assertEqual(respuesta, '/var')


