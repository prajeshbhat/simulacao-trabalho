""" bank02: More Customers """
from SimPy.Simulation import *

## Model components ------------------------             

class Customer(Process):
    """ Customer arrives, looks around and leaves """
        
    def visit(self,timeInBank):       
        print "%7.4f %s: Here I am"%(now(),self.name)   
        yield hold,self,timeInBank
        print "%7.4f %s: I must leave"%(now(),self.name) 

## Experiment data -------------------------

maxTime = 400.0  # minutes                             

## Model/Experiment ------------------------------

initialize()

c1 = Customer(name="Klaus")                              
activate(c1,c1.visit(timeInBank=10.0),at=5.0)
c2 = Customer(name="Tony")
activate(c2,c2.visit(timeInBank=7.0),at=2.0)
c3 = Customer(name="Evelyn")
activate(c3,c3.visit(timeInBank=20.0),at=12.0)         

simulate(until=maxTime)                                
