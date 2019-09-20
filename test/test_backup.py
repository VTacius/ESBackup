# coding: utf-8
import unittest
import sys

import os 
current_path = os.path.dirname(os.path.realpath(__file__))
package_path = '/'.join(current_path.split('/')[:-1])
sys.path.append(package_path)

class obtieneInfoIndice(unittest.TestCase):
    
    # TODO: Ahora es tamaño human-readable
    linea = 'squidguard-activo-2019.06.25         4 22907944660 green open'
    
    def test_tipo(self):
        from backup import obtiene_info_indice

        informacion = obtiene_info_indice(self.linea)
        
        self.assertIsInstance(informacion, tuple)

    def test_division(self):
        from backup import obtiene_info_indice

        informacion = obtiene_info_indice(self.linea)
        
        esperado = ('squidguard-activo-2019.06.25', '2019.06.25', '22907944660', 4, 'activo', 'green', 'open')
        self.assertTupleEqual(informacion, esperado)

    def test_linea_blanco(self):
        from backup import obtiene_info_indice

        informacion = obtiene_info_indice('')

        esperado = (None, None, None, None, None, None, None)
        self.assertTupleEqual(informacion, esperado)

class verificaAntiguedad(unittest.TestCase):
    from datetime import date
    fecha_hoy = date(2019, 5, 15)
    
    def test_mas_antiguo_que_delta(self):
        from backup import verifica_antiguedad

        resultado = verifica_antiguedad(2, self.fecha_hoy, '2019.05.12') 

        self.assertTrue(resultado)
    
    def test_dentro_delta(self):
        from backup import verifica_antiguedad

        resultado = verifica_antiguedad(2, self.fecha_hoy, '2019.05.13') 

        self.assertFalse(resultado)
