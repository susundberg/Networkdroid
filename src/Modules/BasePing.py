

import zmq

from time import sleep

from  multiprocessing import Process

###########################################################################################################
#
###########################################################################################################
class BasePing:
   def __init__( self, log, config):
      self.log     = log
      self.config  = config
      self.socket  = None
      
   def start_module(self):
      process = Process( target = BasePing.work_wrapper, args=(self,) )
      process.daemon = True
      
      process.start()
      
      self.process = process
      
   def terminate(self):
      if self.process != None:
         self.process.terminate()
      
   def sendmessage(self, message ):
      message =  "%s: %s" % (self.__class__.__name__, message )
      self.socket.send( message )
   
   def work_wrapper(self):
     context = zmq.Context(1)
     
     module_socket = context.socket(zmq.PUB) # Output socket
     module_socket.connect( "%s:%s" % (self.config["protocol"], self.config["port_module_sub"]) )
     self.socket = module_socket  
     self.work()

   def work(self):
      self.log.info("Base module running here hey")
      while True:
         self.sendmessage("HB")
         sleep(1)
      
   
   