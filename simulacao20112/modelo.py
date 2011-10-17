# -*- coding: utf-8 -*-

from SimPy.SimulationTrace import *
from dispatch import Signal

## Componentes do Modelo ----------------------

class Caminhao(Process):

    def __init__(self, name, sim):
        Process.__init__(self, name, sim)
        self.property_changed = Signal(providing_args=['property_name'])
        self._t_fila_car = 0.0
        self._t_fila_bal = 0.0
        self._t_ciclo = 0.0


    @property
    def t_fila_car(self):
        return self._t_fila_car

    @t_fila_car.setter
    def t_fila_car(self, value):
        self._t_fila_car = value
        self.property_changed.send(sender=self, property_name='t_fila_car')

    @property
    def t_fila_bal(self):
        return self._t_fila_bal

    @t_fila_bal.setter
    def t_fila_bal(self, value):
        self._t_fila_bal = value
        self.property_changed.send(sender=self, property_name='t_fila_bal')

    @property
    def t_ciclo(self):
        return self._t_ciclo

    @t_ciclo.setter
    def t_ciclo(self, value):
        self._t_ciclo = value
        self.property_changed.send(sender=self, property_name='t_ciclo')
    
    def rodar(self):
        while True:
            # carregando o caminhão
            espera_inicio = self.sim.now()
            yield request, self, self.sim.carregadores
            espera_fim = self.sim.now()
            self.t_fila_car = espera_fim - espera_inicio

            t_carregamento = self.sim.carregamento_va()
            yield hold, self, t_carregamento
            yield release, self, self.sim.carregadores

            # pesagem
            espera_inicio = self.sim.now()
            yield request, self, self.sim.balanca
            espera_fim = self.sim.now()
            self.t_fila_bal = espera_fim - espera_inicio

            t_pesagem = self.sim.pesagem_va()
            yield hold, self, t_pesagem
            yield release, self, self.sim.balanca

            # delay da viagem
            t_viagem = self.sim.viagem_va()
            yield hold, self, t_viagem
            self.t_ciclo = self.t_fila_car + t_carregamento + self.t_fila_bal + t_pesagem + t_viagem
            
            self.sim.nrViagensRealizadas +=1
            
## Modelo -----------------------------------------

class Modelo(Simulation):
    
    def __init__(self, nrCaminhoes=10, tempoSimulacao=1000, maxViagens=None):
        Simulation.__init__(self)
        self.nrCaminhoes_changed = Signal(providing_args=['nrCaminhoes'])
        self.nrCaminhoes = nrCaminhoes
        self.tempoSimulacao = tempoSimulacao
        self.maxViagens = maxViagens
        self.caminhoes = list()

        self.fila_carregadores_changed = Signal(providing_args=['tam'])
        self.carregadores_ativos_changed = Signal(providing_args=['tam'])
        self.fila_balanca_changed = Signal(providing_args=['tam'])
        self.balanca_ativo_changed = Signal(providing_args=['tam'])

        self._carregamento_va = None
        self._pesagem_va = None
        self._viagem_va = None
        self.nrViagensRealizadas_changed = Signal(providing_args=['nrViagensRealizadas'])
        self.caminhao_changed_handler = None
        self._nrViagensRealizadas = 0

    def _nroTotalDeViagensForamRealizadas(self):
        if self.maxViagens is None:
            return false

        return self.nrViagensRealizadas == self.maxViagens

    @property
    def nrCaminhoes(self):
        return self._nrCaminhoes

    @nrCaminhoes.setter
    def nrCaminhoes(self, value):
        self._nrCaminhoes = value
        self.nrCaminhoes_changed.send(sender=self, nrCaminhoes=self._nrCaminhoes)

    @property
    def nrViagensRealizadas(self):
        return self._nrViagensRealizadas

    @nrViagensRealizadas.setter
    def nrViagensRealizadas(self, value):
        self._nrViagensRealizadas = value
        self.nrViagensRealizadas_changed.send(sender=self, nrViagensRealizadas=self._nrViagensRealizadas)
        
        if self._nroTotalDeViagensForamRealizadas():
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

        car_name = 'Carregadores'
        self.carregadores = Resource(name=car_name, unitName='carregador', capacity=2, monitored=True, sim=self)
        carWaitMon = NotifyMonitor(signal= self.fila_carregadores_changed,
                                   name = 'Wait Queue Monitor %s'%car_name,
                                   ylab = 'nr in queue', tlab = 'time',
                                   sim = self)
        print len(self.carregadores.waitQ)
        carWaitMon.observe(t=self.now(), y=len(self.carregadores.waitQ))
        self.carregadores.waitMon = carWaitMon

        carActMon = NotifyMonitor(signal=self.carregadores_ativos_changed,
                                  name = 'Active Queue Monitor %s'%car_name,
                                  ylab = 'nr in queue', tlab = 'time',
                                  sim = self)
        carActMon.observe(t=self.now(), y=len(self.carregadores.activeQ))
        self.carregadores.actMon = carActMon

        bal_name = 'Balança'
        self.balanca = Resource(name=bal_name, unitName='balança', capacity=1, monitored=True, sim=self)
        balWaitMon = NotifyMonitor(signal=self.fila_balanca_changed,
                                   name = 'Wait Queue Monitor %s'%bal_name,
                                   ylab = 'nr in queue', tlab = 'time',
                                   sim = self)
        balWaitMon.observe(t=self.now(), y=len(self.balanca.waitQ))
        self.balanca.waitMon = balWaitMon

        balActMon = NotifyMonitor(signal=self.balanca_ativo_changed,
                                  name = 'Active Queue Monitor %s'%bal_name,
                                  ylab = 'nr in queue', tlab = 'time',
                                  sim = self)
        balActMon.observe(t=self.now(), y=len(self.balanca.activeQ))
        self.balanca.actMon = balActMon

        for i in range(self._nrCaminhoes):
            caminhao = Caminhao(name='caminhao_%s'%i, sim=self)
            caminhao.property_changed.connect(self.caminhao_changed_handler)
            self.caminhoes.append(caminhao)
            self.activate(caminhao, caminhao.rodar())

        self.simulate(until=1000)

class NotifyMonitor(Monitor):

    def __init__(self, signal, **kwargs):
        Monitor.__init__(self, **kwargs)
        self.monitor_changed = signal
    
    def observe(self, y, t=None):
        Monitor.observe(self, y=y, t=t)
        self.monitor_changed.send(sender=self, tam=y)
        

class Estatisticas:

    class MinMaxMedia:
        def __init__(self, property_changed):
            self._min = 0.0
            self._max = 0.0
            self._media = 0.0
            self._count = 0
            self.property_changed = property_changed

        def verify_and_notify(self, attr_name, value):
            if getattr(self, attr_name) != value:
                setattr(self, attr_name, value)
                self.property_changed.send(sender=self, property_name=attr_name[1:])

        def update_properties(self, val, average=None):
            self.min = min(self.min, val)
            self.max = max(self.max, val)
            self._count += 1
            if average is None:
                self.media = (self.media + val) / self._count
            else:
                self.media = average

        @property
        def min(self):
            return self._min

        @min.setter
        def min(self, value):
            self.verify_and_notify('_min', value)

        @property
        def max(self):
            return self._max

        @max.setter
        def max(self, value):
            self.verify_and_notify('_max', value)

        @property
        def media(self):
            return self._media

        @media.setter
        def media(self, value):
            self._media = value
            self.property_changed.send(sender=self, property_name='media')



    def __init__(self, modelo):
        self.property_changed = Signal(providing_args=['property_name'])

        self._tam_fila_carregadores = MinMaxMedia(self.property_changed)
        modelo.fila_carregadores_changed.connect(fila_carregadores_changed)

        self._tam_fila_balanca = MinMaxMedia(self.property_changed)
        modelo.fila_balanca_changed.connect(fila_balanca_changed)

        self._ocupacao_media_car = 0.0
        modelo.carregadores_ativos_changed.connect(carregadores_ativos_changed)
        self._ocupacao_media_bal = 0.0
        modelo.balanca_ativo_changed.connect(balanca_ativo_changed)

        modelo.caminhao_changed_handler = self.caminhao_changed_handler
        self._tempo_fila_carregador = MinMaxMedia(self.property_changed)
        self._tempo_fila_balanca = MinMaxMedia(self.property_changed)
        self._tempo_ciclo = MinMaxMedia(self.property_changed)

    @property
    def ocupacao_media_car(self):
        return self._ocupacao_media_car

    @ocupacao_media_car.setter
    def ocupacao_media_car(self, value):
        self._ocupacao_media_car = value
        self.property_changed.send(sender=self, property_changed='ocupacao_media_car')

    @property
    def ocupacao_media_bal(self):
        return self._ocupacao_media_bal

    @ocupacao_media_bal.setter
    def ocupacao_media_bal(self, value):
        self._ocupacao_media_bal = value
        self.property_changed.send(sender=self, property_changed='ocupacao_media_bal')

    def caminhao_changed_handler(self, sender, **kwargs):
        property_changed_name = kwargs['property_name']
        property_value = getattr(sender, property_changed_name)
        if property_changed_name == 't_fila_car':
            self._tempo_fila_carregador.update_properties(property_value)
        elif property_changed_name == 't_fila_bal':
            self._tempo_fila_balanca.update_properties(property_value)
        elif property_changed_name == 't_ciclo':
            self._tempo_ciclo.update_properties(property_value)

    def fila_carregadores_changed(self, sender, **kwargs):
        tam_atual = kwargs['tam']
        average = sender.timeaverage()
        self._tam_fila_carregadores.update_properties(tam_atual, average)
            
    def fila_balanca_changed(self, sender, **kwargs):
        tam_atual = kwargs['tam']
        average = sender.timeaverage()
        self._tam_fila_balanca.update_properties(tam_atual, average)

    def carregadores_ativos_changed(self, sender, **kwargs):
        self.ocupacao_media_car = sender.timeaverage()
        
    def balanca_ativo_changed(self, sender, **kwargs):
        self.ocupacao_media_bal = sender.timeaverage()
        
