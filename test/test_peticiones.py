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

