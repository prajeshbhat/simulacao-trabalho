#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from SimPy.Simulation import *
from SimPy.SimGUI import *
import random, re

distribuicoes = ['uniforme', 'normal', 'exponencial']

##  distribution factory
def makeDistribution(function,*pars):
    def distribution():
        return function(*pars)
    return distribution

## Componentes do modelo

class Embalador(Process):
    def __init__(self, reiniciarEv, nome='Embalador'):
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

    def __init__(self, embalador, nome='Falha'):
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
    def __init__(self, reiniciarEv, nome='Demanda'):
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
    # pergunta t_simulacao TODO
    top = Toplevel(root)

    modelo = Modelo()
    modelo.capacidade = gui.capacidade_obj

class MinhaGUI(SimGUI):
    entryText = {
        'capacidade': 'Capacidade do armazém',
        'num_produtos': 'Número de produtos embalados',
        'reabastecimento': 'Ponto de reabastecimento',
        'process_va': 'Tempo de processamento do empacotamento',
        'process_va_sem': 'Semente do temp. de proc.',
        'reparo_va': 'Tempo de reparo do empacotador',
        'reparo_va_sem': 'Semente do tempo de reparo',
        'tef_va': 'Tempo entre falhas',
        'tef_va_sem': 'Semente do tempo entre falhas',
        'tec_va': 'Tempo entre chegada de clientes',
        'tec_va_sem': 'Semento do tempo entre chegada',
        'demanda_va': 'Número de produtos da demanda',
        'demanda_va_sem': 'Semente do núm. de produtos da demanda'
        }
    
    def __init__(self, win, **p):
        SimGUI.__init__(self, win, p)
        self.run.add_command(label='executar modelo', command=run)
        self.view.add_command(label='estatísticas', command=estatisticas)

        self.intDistr2funcName = {'uniforme' : 'randint', 'normal': 'normalvariate', 'exponencial': 'expovariate', 'triangular': 'triangular'}
        self.floatDistr2funcName = dict(self.intDistr2funcName)
        self.floatDistr2funcName['uniforme'] = 'uniform'
        
        pat_str_template = r'(?P<nome>uniforme|normal|exponencial|triangular)\s*\((?P<valores>\s*{numero}\s*(?:,\s*{numero}\s*)*)\)'
        int_pat_str = r'\d+'
        float_pat_str = r'(\d+(?:\.\d*)?|\.\d+)'

        self.int_distributions_pat = re.compile(pat_str_template.format(numero=int_pat_str), re.VERBOSE)
        self.float_distributions_pat = re.compile(pat_str_template.format(numero=float_pat_str), re.VERBOSE)

        self.capacidade = IntVar()
        self.capacidade.set(1000)

        self.num_produtos = IntVar()
        self.num_produtos.set(3)

        self.reabastecimento = IntVar()
        self.reabastecimento.set(700)

        self.process_va = StringVar()
        self.process_va.set('exponencial(2.5)')

        self.process_va_sem = IntVar()
        self.process_va_sem.set(42)

        self.reparo_va = StringVar()
        self.reparo_va.set('uniforme(1, 3.5)')

        self.reparo_va_sem = IntVar()
        self.reparo_va_sem.set(3)

        self.tef_va = StringVar()
        self.tef_va.set('triangular(30, 70, 43)')

        self.tef_va_sem = IntVar()
        self.tef_va_sem.set(37)

        self.tec_va = StringVar()
        self.tec_va.set('exponencial(7.2)')

        self.tec_va_sem = IntVar()
        self.tec_va_sem.set(3487)

        self.demanda_va = StringVar()
        self.demanda_va.set('uniforme(2, 6)')

        self.demanda_va_sem = IntVar()
        self.demanda_va_sem.set(234)


    def changeParameters(self):
        self.paramWindow = Toplevel(self.root)
        top = Frame(self.paramWindow)

        self.paramLabels = {}
        self.paramEntries = {}

        self.paramLabels['capacidade'] = Label(top, text='Capacidade do armazém')
        self.paramLabels['capacidade'].grid(row=0, column=0, sticky=E)
        self.paramEntries['capacidade'] = Entry(top, textvariable=self.capacidade)
        self.paramEntries['capacidade'].grid(row=0, column=1, sticky=W)

        self.paramLabels['num_produtos'] = Label(top, text='Número de produtos embalados')
        self.paramLabels['num_produtos'].grid(row=2, column=0, sticky=E)
        self.paramEntries['num_produtos'] = Entry(top, textvariable=self.num_produtos)
        self.paramEntries['num_produtos'].grid(row=2, column=1, sticky=W)

        self.paramLabels['reabastecimento'] = Label(top, text='Ponto de reabastecimento')
        self.paramLabels['reabastecimento'].grid(row=4, column=0, sticky=E)
        self.paramEntries['reabastecimento'] = Entry(top, textvariable=self.reabastecimento)
        self.paramEntries['reabastecimento'].grid(row=4, column=1, sticky=W)


        self.paramLabels['process_va'] = Label(top, text='Tempo de processamento do empacotamento')
        self.paramLabels['process_va'].grid(row=6, column=0, sticky=E)
        self.paramEntries['process_va'] = Entry(top, textvariable=self.process_va)
        self.paramEntries['process_va'].grid(row=6, column=1, sticky=W)

        self.paramLabels['process_va_sem'] = Label(top, text='Semente')
        self.paramLabels['process_va_sem'].grid(row=7, column=0, sticky=E)
        self.paramEntries['process_va_sem'] = Entry(top, textvariable=self.process_va_sem)
        self.paramEntries['process_va_sem'].grid(row=7, column=1, sticky=W)


        self.paramLabels['reparo_va'] = Label(top, text='Tempo de reparo do empacotador')
        self.paramLabels['reparo_va'].grid(row=9, column=0, sticky=E)
        self.paramEntries['reparo_va'] = Entry(top, textvariable=self.reparo_va)
        self.paramEntries['reparo_va'].grid(row=9, column=1, sticky=W)

        self.paramLabels['reparo_va_sem'] = Label(top, text='Semente')
        self.paramLabels['reparo_va_sem'].grid(row=10, column=0, sticky=E)
        self.paramEntries['reparo_va_sem'] = Entry(top, textvariable=self.reparo_va_sem)
        self.paramEntries['reparo_va_sem'].grid(row=10, column=1, sticky=W)


        self.paramLabels['tef_va'] = Label(top, text='Tempo entre falhas')
        self.paramLabels['tef_va'].grid(row=12, column=0, sticky=E)
        self.paramEntries['tef_va'] = Entry(top, textvariable=self.tef_va)
        self.paramEntries['tef_va'].grid(row=12, column=1, sticky=W)

        self.paramLabels['tef_va_sem'] = Label(top, text='Semente')
        self.paramLabels['tef_va_sem'].grid(row=13, column=0, sticky=E)
        self.paramEntries['tef_va_sem'] = Entry(top, textvariable=self.tef_va_sem)
        self.paramEntries['tef_va_sem'].grid(row=13, column=1, sticky=W)


        self.paramLabels['tec_va'] = Label(top, text='Tempo entre chegada de clientes')
        self.paramLabels['tec_va'].grid(row=15, column=0, sticky=E)
        self.paramEntries['tec_va'] = Entry(top, textvariable=self.tec_va)
        self.paramEntries['tec_va'].grid(row=15, column=1, sticky=W)

        self.paramLabels['tec_va_sem'] = Label(top, text='Semente')
        self.paramLabels['tec_va_sem'].grid(row=16, column=0, sticky=E)
        self.paramEntries['tec_va_sem'] = Entry(top, textvariable=self.tec_va_sem)
        self.paramEntries['tec_va_sem'].grid(row=16, column=1, sticky=W)


        self.paramLabels['demanda_va'] = Label(top, text='Número de produtos da demanda')
        self.paramLabels['demanda_va'].grid(row=18, column=0, sticky=E)
        self.paramEntries['demanda_va'] = Entry(top, textvariable=self.demanda_va)
        self.paramEntries['demanda_va'].grid(row=18, column=1, sticky=W)
        
        self.paramLabels['demanda_va_sem'] = Label(top, text='Semente')
        self.paramLabels['demanda_va_sem'].grid(row=19, column=0, sticky=E)
        self.paramEntries['demanda_va_sem'] = Entry(top, textvariable=self.demanda_va_sem)
        self.paramEntries['demanda_va_sem'].grid(row=19, column=1, sticky=W)

        top.pack(side=TOP,fill=BOTH,expand=YES)                                                    
        commitBut=Button(top,text='Mudar parâmetros',command=self.commit)
        commitBut.grid(row=21, column=1)

    
    def commit(self):
        entrada_tmp = dict()
        var_aleatorias = ['process_va', 'demanda_va', 'reparo_va', 'tef_va', 'tec_va']
        
        for k in self.paramEntries:
            try:
                if k in var_aleatorias:
                    entrada_tmp[k] = getattr(self, k).get()

            except ValueError:
                entradaCorreta = False
                showerror(title='Erro de entrada', message='O parâmetro "%s" está errado.' % self.entryText[k])
                return

        for disc_attr in var_aleatorias:
            m = self.int_distributions_pat.match(var_aleatorias[disc_attr]) \
                if disc_attr in ['process_va', 'demanda_va']  else \
                self.float_distributions_pat.match(var_aleatorias[disc_attr])
            if m:
                try:
                    distr_k = m.group('nome')
                    distrMethodName = intDistr2funcName[distr_k] if disc_attr in ['process_va', 'demanda_va'] else floatDistr2funcName[distr_k]
                    rand = random.Random(getattr(self, disc_attr+'_sem_obj'))
                    nome_atributo = disc_attr+'_obj'
                    setattr(self, nome_atributo, eval('makeDistribution(rand.' + 'distrMethodName, ' + m.group('valores')))
                except:
                    entradaCorreta = False
                    showerror(title='Erro de entrada', message='A expressão da VA "%s" está errada' % self.entryText[disc_attr])
                    return
                            
        self.paramWindow.destroy()
                            


root = Tk()
gui = MinhaGUI(root, title="Simulação do sistema de embalamento")
gui.mainloop()
