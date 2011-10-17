# -*- coding: utf-8 -*-

import unittest
import modelo

class ModeloSpy:
    pass

class ModeloTest(unittest.TestCase):

    def setUp(self):
        self.modelo1 = Modelo()
        self.spy1 = ModeloSpy()
        
        self.modelo1.carregamento_va = lambda: 10
        self.modelo1.pesagem_va = lambda: 10
        self.modelo1.viagem_va = lambda: 10

        
        
    
    # 1 caminhão, 
    def test_1_caminhao(self):
        self.modelo1.nrCaminhoes = 1
        
