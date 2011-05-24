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
    def __init__(self, nome='Embalador', reiniciarEv):
        Process.__init__(self, nome)
        self.reiniciarEvent = reiniciarEv

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
                espaco_restante = estoque.capacity - estoque.amount
                yield put, self, estoque, espaco_restante
                # TODO: esperar até que o nível do estoque caia para o ponto de reabastecimento r
                yield waitevent, self, self.reiniciarEvent

class Falha(Process):

    def __init__(self, nome='Falha', embalador):
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
    def __init__(self, nome='Demanda', reiniciarEv):
        Process.__init__(self, nome)
        self.demandaSatisfeitaMon = Monitor(name="Demanda atendida dos clientes")
        self.reiniciarEvent = reiniciarEv

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
class Modelo:
    def __init__(self):
        self._capacidade = None
        self._num_produtos = None
        self._t_simulacao = None
        self._reabastecimento = None
        self._process_va = None
        self._reparo_va = None
        self._tef_va = None
        self._tec_va = None
        self._demanda_va = None

        

    @property
    def capacidade(self):
        return self._capacidade

    @capacidade.setter
    def capacidade(self, value):
        self._capacidade = value
        

    @property
    def num_produtos(self):
        return self._num_produtos

    @num_produtos.setter
    def num_produtos(self, value):
        self._num_produtos = value


    @property
    def reabastecimento(self):
        return self._reabastecimento

    @reabastecimento.setter
    def reabastecimento(self, value):
        self._reabastecimento = value


    @property
    def process_va(self):
        return self._process_va

    @process_va.setter
    def process_va(self, func):
        self._process_va = func


    @property
    def reparo_va(self):
        return self._reparo_va

    @reparo_va.setter
    def reparo_va(self, func):
        self._reparo_va = func


    @property
    def tef_va(self):
        return self._tef_va

    @tef_va.setter
    def tef_va(self, func):
        self._tef_va = func


    @property
    def tec_va(self):
        return self._tec_va
    
    @tec_va.setter
    def tec_va(self, func):
        self._tec_va = func


    @property
    def demanda_va(self):
        return self._demanda_va

    @demanda_va.setter
    def demanda_va(self, func):
        self._demanda_va = func


    def executar(self, t_simulacao=1000):
        initialize()
        reiniciarEvent = SimEvent('Reiniciar reposição')
        estoque = Level(name="Armazém", capacity=self._capacidade, monitored=True, monitorType=Monitor)
        emb = Embalador(reiniciarEv=reiniciarEvent)
        activate(emb, emb.operar(self._num_produtos, estoque, self._process_va, self._reparo_va))
        falha = Falha(embalador=emb)
        activate(falha, falha.falhar(self._tef_va))
        demanda = Demanda(reiniciarEv=reiniciarEvent)
        activate(demanda, demanda.obter(estoque, self._tec_va, self._demanda_va, self._reabastecimento))

        simulate(until=t_simulacao)


## Estatísticas

def estatisticas():
    pass # TODO


def run():
"""Faz o parsing das opções passadas.

"""

class MinhaGUI(SimGUI):
    def __init__(self, win, **p):
        SimGUI.__init__(self, win, p)
        self.run.add_command(label='executar modelo', command=run)
        self.view.add_command(label='estatísticas', command=estatisticas)

        self.params = Parameters()

    def changeParameters(self):
        self.findParameters()
        if not self._parameters:
            showwarning("SimGUI warning","No Parameters instance found.") 
            return
        self.paramWindow=Toplevel(self.root)
        top=Frame(self.paramWindow)
        self.lbl={}
        self.ent={}
        i=1
        for p in self._parameters.__dict__.keys():
            self.lbl[p]=Label(top,text=p)
            self.lbl[p].grid(row=i,column=0)
            self.ent[p]=Entry(top)
            self.ent[p].grid(row=i,column=1)
            self.ent[p].insert(0,self._parameters.__dict__[p])
            i+=1
        top.pack(side=TOP,fill=BOTH,expand=YES)
        commitBut=Button(top,text='Change parameters',command=self.commit)
        commitBut.grid(row=i,column=1)



    def commit(self):
        entradaCorreta = False
        for p in self._parameters.__dict__.keys():
            entrada = getattr(self._parameters, p)
            if p == 'reabastecimento':
                try:
                    setattr(self._parameters, p, int(self.ent[p].get()))
                except ValueError:
                    showerror(title='Erro de entrada', message)
                    break
                
            elif p == '':
                pass
        else:
            entradaCorreta = True
                
        if entradaCorreta:
            self.paramWindow.destroy()


root = Tk()
gui = MinhaGUI(root, title="Simulação do sistema de embalamento")
gui.mainloop()
