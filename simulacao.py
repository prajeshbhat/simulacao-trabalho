#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from SimPy.Simulation import *
import random

##  distribution factory
def makeDistribution(function,*pars):
    def distribution():
        return function(*pars)
    return distribution

## Componentes do modelo

class Embalador(Process):
    def __init__(self, nome, estoque_capacidade, reiniciarEvent):
        Process.__init__(self, nome)
        self.reiniciarEvent = reiniciarEvent
        self.estoque_capacidade = estoque_capacidade

    def operar(self, num_produtos, estoque, process_va, reparo_va): # PEM
        """Process Execution Method do embalador.

        Argumentos:
        num_produtos: número de produtos embalados
        estoque: objeto Level que representa o armazém
        process_va: função de distribuição de probabilidade da variável aleatória 'tempo de processamento do embalamento'
        reparo_va: função de distribuição de probabilidade da variável aleatória 'tempo de reparo do embalador'
    
        """
        while True:
            yield hold, self, process_va()
            if self.interrupted():
                t_restante = self.interruptLeft
                self.interruptReset()
                t_reparo = reparo_va()
                reactivate(self.interruptCause, delay=t_reparo)
                # reparando o sistema
                yield hold, self, t_reparo
                # terminando o processo de embalamento
                yield hold, self, t_restante

            yield (put, self, estoque, num_produtos), (hold, self, 0)
            if self.stored(estoque):
                pass
            else:
                espaco_restante = self.estoque_capacidade - estoque.amount
                yield put, self, estoque, espaco_restante
                # TODO: esperar até que o nível do estoque caia para o ponto de reabastecimento r
                yield waitevent, self, self.reiniciarEvent

class Falha(Process):

    def __init__(self, nome, embalador):
        Process.__init__(self, nome)
        self.embalador = embalador

    def falhar(self, tef_va): # PEM
        """Processo que simula falhas na máquina embaladora.

        Argumentos:
        tef_va: função de distribuição de probabilidade da variável aleatória 'tempo entre falhas'
        
        """
        while True:
            yield hold, self, tef_va()
            if self.embalador.terminated():
                break

            self.interrupt(self.embalador)


class Demanda(Process):
    def __init__(self, nome, reiniciarEvent):
        Process.__init__(self, nome)
        self.demandaSatisfeitaMon = Monitor(name="Demanda atendida dos clientes")
        self.reiniciarEvent = reiniciarEvent

    def obter(self, estoque, tec_va, demanda_va, reabastecimento): # PEM
        """
        Argumentos:
        estoque: objeto Level que representa o armazém.
        tec_va: função de distribuição de probabilidade da variável aleatória 'tempo entre chegadas de clientes'.
        demanda_va: função de distribuição de probabilidade da variável aleatória 'número de produtos da demanda'.
        reabastecimento: inteiro que representa o nível de reposição do armazém. Usado para reiniciar o processo de embalamento.
        
        """
        while True:
            # esperar pelo próximo cliente
            yield hold, self, tec_va()
            # o cliente pega os produtos
            num_demanda = demanda_va()
            quant = num_demanda
            yield (get, self, estoque, num_demanda), (hold, self, 0)
            t_now = now()
            if self.acquired(estoque):
                self.demandaSatisfeitaMon.observe(1.0, t_now) # 100% atendido
            else:
                quant = estoque.amount
                yield get, self, estoque, quant
                self.demandaSatisfeitaMon.observe(float(quant)/num_demanda, t_now)

            if quant >= reabastecimento:
                self.reiniciarEvent.signal()


## Modelo

def modelo(capacidade, num_produtos, t_simulacao, reabastecimento):
    """
    Argumentos:
    capacidade: capacidade máxima do armazém
    num_produtos: número de produtos embalados
    reabastecimento: inteiro que representa o nível de reposição do armazém. Usado para reiniciar o processo de embalamento.
    
    """
    initialize()
    reiniciarEvent = SimEvent('Reiniciar reposição')
    estoque = Level(name="Armazém", capacity=capacidade, monitored=True, monitorType=Monitor)
    embalador = Embalador("embalador", capacidade, reiniciarEvent)
    activate(embalador, embalador.operar(num_produtos, estoque))
    falha = Falha("Falha", embalador)
    activate(falha, falha.falhar())
    demanda = Demanda("Demanda", reiniciarEvent)
    activate(demanda, demanda.obter(estoque))
    
    simulate(until=t_simulacao)


## Estatísticas

def estatisticas():
    pass # TODO


class MinhaGUI(SimGUI):
    def __init__(self, win, **p):
        SimGUI.__init__(self, win, p)
        self.run.add_command(label='executar modelo', command=run)
        self.view.add_command(label='estatísticas', command=estatisticas)

        self.params = Parameters()


root = Tk()
gui = MinhaGUI(root, title="Simulação do sistema de embalamento")
gui.mainloop()
