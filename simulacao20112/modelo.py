# -*- coding: utf-8 -*-

from SimPy.Simulation import *

class Caminhao(Process):
    
    def __init__(self, name, sim):
        Process.__init__(self, name=name, sim=sim)

    def rodar(self):
        while True:
            # carregando o caminhão
            yield request, self, self.sim.carregadores
            yield hold, self, self.sim.carregamento_va()
            yield release, self, self.sim.carregadores

            # pesagem
            yield request, self, self.sim.balanca
            yield hold, self, self.sim.pesagem_va()
            yield release, self, self.sim.balanca

            # delay da viagem
            yield hold, self, self.sim.viagem_va()
            
            self.sim.nrViagensRealizadas +=1
            


class Modelo(Simulation):
    
    def __init__(self, nrCaminhoes=10, tempoSimulacao=1000, maxViagens=None):
        Simulation.__init__(self)
        self.nrCaminhoes = nrCaminhoes
        self.tempoSimulacao = tempoSimulacao
        self.maxViagens = maxViagens
        self.caminhoes = list()
        self._carregamento_va = None
        self._pesagem_va = None
        self._viagem_va = None

    def nroTotalDeViagensForamRealizadas(self):
        if maxViagens is None:
            return false

        return self.nrViagensRealizadas == self.maxViagens

    @property
    def nrViagensRealizadas(self):
        return self._nrViagensRealizadas

    @nrViagensRealizadas.setter
    def nrViagensRealizadas(self, value):
        self._nrViagensRealizadas = value
        
        if nroTotalDeViagensForamRealizadas(self):
            self.stopSimulation()

    @property
    def carregamento_va(self):
        return self._carregamento_va

    @carregamento_va.setter
    def carregamento_va(self, value):
        self._carregamento_va = value

    @property
    def pesagem_va(self):
        return self._pesagem_va

    @pesagem_va.setter
    def pesagem_va(self, value):
        self._pesagem_va = value

    @property
    def viagem_va(self):
        return self._viagem_va
        
    @viagem_va.setter
    def viagem_va(self, value):
        self._viagem_va = value

    def rodar(self):
        self.nrViagensRealizadas = 0
        self.initialize()
        self.carregadores = Resource(name='Carregadores', unitName='carregador', capacity=2, sim=self)
        self.balanca = Resource(name='Balança', unitName='balança', capacity=1, sim=self)

        for i in range(self.nrCaminhoes):
            caminhao = Caminhao(name='caminhao_%s'%i, sim=self)
            self.caminhoes.append(caminhao)
            self.activate(caminhao, caminhao.rodar())

        self.simulate(until=1000)
