"""bank16_OO: Plotting from  Resource Monitors"""
from SimPy.Simulation import *
from SimPy.SimPlot import *                                   
from random import expovariate,seed

## Model components ------------------------           

class Source(Process):                                        
    """ Source generates customers randomly"""
    def generate(self,number,rate):       
        for i in range(number):
            c = Customer(name = "Customer%02d"%(i,),sim=self.sim)
            self.sim.activate(c,c.visit(timeInBank=12.0))
            yield hold,self,expovariate(rate)

class Customer(Process):                                      
    """ Customer arrives, is served and leaves """
    def visit(self,timeInBank):       
        arrive = self.sim.now()
        #print "%8.4f %s: Arrived     "%(now(),self.name)

        yield request,self,self.sim.counter
        #print "%8.4f %s: Got counter "%(now(),self.name)
        tib = expovariate(1.0/timeInBank)
        yield hold,self,tib
        yield release,self,self.sim.counter

        #print "%8.4f %s: Finished    "%(now(),self.name)

## Experiment data -------------------------

maxTime = 400.0   # minutes                                    
           

## Model -----------------------------------

class BankModel(Simulation):                                      
    def run(self):
        self.initialize()
        self.counter = Resource(1,name="Clerk",monitored=True,sim=self) 
        source = Source(sim=self)                                                         
        self.activate(source,
             source.generate(number=20,rate=0.1),at=0.0)    
        self.simulate(until=maxTime)                                    

## Experiment -----------------------------------
seed(393939)
modl=BankModel()
modl.run()
 
## Output ---------------------------------------
plt = SimPlot()                                                  
plt.plotStep(modl.counter.waitMon,                                  
        color="red",width=2)                                   
plt.mainloop()                                                 
