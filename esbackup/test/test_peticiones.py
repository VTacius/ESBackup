"""Pruebas para nuestra implementación de Request en esbackup.peticiones"""
import unittest
import requests_mock


class PeticionesGet(unittest.TestCase):

    url = 'http://test.com'

    @requests_mock.Mocker()
    def test_get_peticiones(self, mockup):
        """¿Funciona _peticionar como se espera por defecto, regresando JSON"""
        from esbackup import peticiones

        mockup.get(self.url, json={})

        respuesta = peticiones._peticionar('get', self.url)

        self.assertEqual(respuesta, {})

    @requests_mock.Mocker()
    def test_get_peticion_json(self, mockup):
        """¿Funciona _peticionar como se espera al pedir texto plano"""
        from esbackup import peticiones

        mockup.get(self.url, text='')

        respuesta = peticiones._peticionar('get', self.url, respuesta_tipo='texto')

        self.assertEqual(respuesta, [''])
