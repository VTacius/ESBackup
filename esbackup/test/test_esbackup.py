import unittest

class TestClasificarIndices(unittest.TestCase):
    indices = [
        'auditbeat-activo-2019.06.09     5000', 
        'auditbeat-activo-2019.06.10     4000', 
        'auditbeat-activo-2019.06.11    10187', 
        'auditbeat-activo-2019.06.12     5570', 
        'auditbeat-activo-2019.06.13     5194', 
        'auditbeat-activo-2019.06.14     3523', 
        'auditbeat-activo-2019.06.15     4226', 
        'squid-activo-2019.06.29        10000', 
        'squid-activo-2019.06.30        10000', 
        'squid-activo-2019.07.01        46727', 
        'squid-activo-2019.07.02        38402', 
        'squid-activo-2019.07.03        27210', 
        'squid-activo-2019.07.04        26893', 
        'squid-activo-2019.07.05        44952', 
        'squidguard-activo-2019.05.08    5000', 
        'squidguard-activo-2019.05.09    6000', 
        'squidguard-activo-2019.05.10     916', 
        'squidguard-activo-2019.05.11     869', 
        'squidguard-activo-2019.05.12     164', 
        'squidguard-activo-2019.05.13    6148', 
        'squidguard-activo-2019.05.14    7820', 
    ]
    
    def test_espacio_requerido(self):
        from esbackup.cli import calcular_espacio_requerido
        resultado = calcular_espacio_requerido(1000, 0.2, 2500, 500) 

        self.assertEqual(resultado, 1000)
    
    def test_espacio_requerido_libre_ayuda(self):
        from esbackup.cli import calcular_espacio_requerido
        resultado = calcular_espacio_requerido(1000, 0.2, 1500, 1000) 

        self.assertEqual(resultado, 450)
    
    def test_espacio_requerido_libre_mayor(self):
        from esbackup.cli import calcular_espacio_requerido
        resultado = calcular_espacio_requerido(1000, 0.2, 500, 2500) 

        self.assertEqual(resultado, 0)

    def test_espacio_usado_indices(self):
        from esbackup.esbackup import espacio_usado_indices 
        from esbackup.esbackup import clasificar_indices
        tabla = clasificar_indices(self.indices)
        resultado = espacio_usado_indices(tabla, 1)

        self.assertEqual(2000, resultado)
    
    def test_espacio_usado_indices(self):
        from esbackup.esbackup import espacio_usado_indices 
        from esbackup.esbackup import clasificar_indices
        tabla = clasificar_indices(self.indices)
        resultado = espacio_usado_indices(tabla, 2)

        self.assertEqual(20000, resultado)

    def test_clasificar_indices(self):
        from esbackup.esbackup import clasificar_indices
        resultado = clasificar_indices(self.indices)
        resultado =  list(resultado.keys())
        resultado.sort()
        self.assertListEqual(['auditbeat', 'squid', 'squidguard'], resultado)
    
    def test_clasificar_indices_tipo(self):
        from esbackup.esbackup import clasificar_indices
        
        resultado = clasificar_indices(self.indices)
        resultado = resultado['auditbeat'][0]
        
        self.assertTrue(isinstance(resultado, tuple))
    
    def test_clasificar_indices_contenido(self):
        from esbackup.esbackup import clasificar_indices
        
        resultado = clasificar_indices(self.indices)
        resultado = resultado['auditbeat'][0]
        
        self.assertEqual(('auditbeat-activo-2019.06.09', 5000), resultado)
   
    def test_seleccionar_indices_a_borrar(self):
        from esbackup.esbackup import clasificar_indices
        from esbackup.esbackup import seleccionar_indices_a_borrar
   
        indices = clasificar_indices(self.indices) 
        resultado = seleccionar_indices_a_borrar(2, 20000, indices)
        resultado.sort() 
        
        self.assertListEqual(['auditbeat-activo-2019.06.09', 'squid-activo-2019.06.29','squidguard-activo-2019.05.08'], resultado) 
    
    def test_seleccionar_indices_a_borrar_caso2(self):
        from esbackup.esbackup import clasificar_indices
        from esbackup.esbackup import seleccionar_indices_a_borrar
   
        indices = clasificar_indices(self.indices) 
        resultado = seleccionar_indices_a_borrar(2, 40000, indices)
        resultado.sort() 
        
        self.assertListEqual(
                ['auditbeat-activo-2019.06.09', 'auditbeat-activo-2019.06.10', 'squid-activo-2019.06.29', 'squid-activo-2019.06.30', 'squidguard-activo-2019.05.08', 'squidguard-activo-2019.05.09'], 
                resultado) 
    
    def test_seleccionar_indices_a_borrar_limite(self):
        from esbackup.esbackup import clasificar_indices
        from esbackup.esbackup import seleccionar_indices_a_borrar
   
        indices = clasificar_indices(self.indices) 
        resultado = seleccionar_indices_a_borrar(5, 60000, indices)
        resultado.sort() 
        
        self.assertListEqual(['auditbeat-activo-2019.06.09', 'auditbeat-activo-2019.06.10', 'squid-activo-2019.06.29', 'squid-activo-2019.06.30', 'squidguard-activo-2019.05.08', 'squidguard-activo-2019.05.09'], resultado) 
    

