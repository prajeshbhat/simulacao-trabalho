# -*- coding: utf-8 -*-

import unittest
import modelo


class ModeloSpy:
    pass

class ModeloTest(unittest.TestCase):

    def setUp(self):
        self.modelo1 = modelo.Modelo()
        self.spy1 = ModeloSpy()
        
        self.modelo1.carregamento_va = lambda: 10
        self.modelo1.pesagem_va = lambda: 10
        self.modelo1.viagem_va = lambda: 10

        
        
    
    # 1 caminhão, 1 viagem
    def test_1_caminhao_1_viagem(self):
        self.modelo1.nrCaminhoes = 1
        self.modelo1.maxViagens = 1
        self.modelo1.rodar()
        
        self.assertEqual(1, self.modelo1.nrViagensRealizadas)


if __name__ == '__main__':
    unittest.main()
