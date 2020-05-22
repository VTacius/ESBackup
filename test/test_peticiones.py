#coding: utf-8

import unittest
import requests_mock

from json import dumps

class PeticionesGet (unittest.TestCase):

    url = 'http://test.com'
    
    @requests_mock.Mocker()
    def test_get_peticiones(self, m):
        from elastica import peticiones 
        
        m.get(self.url, json={})
        
        respuesta = peticiones._peticionar('get', self.url) 

        self.assertEqual(respuesta, {})
    
    @requests_mock.Mocker()
    def test_get_peticion_json(self, m):
        from elastica import peticiones

        m.get(self.url, text='')

        respuesta = peticiones._peticionar('get', self.url, respuesta_tipo = 'texto')

        self.assertEqual(respuesta, [''])

    @requests_mock.Mocker()
    def test_get_peticion_error(self, m):
        from elastica import peticiones
        contenido_error = {
                'error': {
                    'type': 'Tipo de error',
                    'reason': 'Razón del error' 
                    } 
                } 
        m.get(self.url, json=contenido_error, status_code=404)
        
        respuesta = peticiones._peticionar('get', self.url) 

        self.assertFalse(respuesta)
