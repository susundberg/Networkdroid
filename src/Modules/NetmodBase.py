

import zmq

from time import sleep
from  multiprocessing import Process

###########################################################################################################
#
###########################################################################################################
class NetmodBase:
   def __init__( self, log, config, parameters ):
      self.log     = log
      self.config  = config
      self.socket  = None
      self.parameters = parameters
      self.process  = None
      self.timestep = 0
      
   def start_module(self):
      process = Process( target = NetmodBase.work_wrapper, args=(self,) )
      process.daemon = True
      process.start()
      self.process = process
   
   def has_died(self):
      self.timestep = self.timestep + 1
      
      print "Query on " + self.__class__.__name__
      
      if self.timestep == 1:
         return False
      
      if self.process and self.process.is_alive() == True:
        return False
      return True
   
   def terminate(self):
      if self.process != None:
         self.process.terminate()
         
   
   def send_error( self, message ):
      self.log.error("Error on module %s : %s " % (self.__class__.__name__, message ) )
      self.send_message( "ERROR: message")
      
   def send_message(self, message ):
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
      
      if len(self.parameters) > 0:
         self.send_error("Base module does not accept parameters.")
         return False
      
      while True:
         self.send_message("HB")
         sleep(1)
      
   
   