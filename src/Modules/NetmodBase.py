

import zmq

from time import sleep
from  multiprocessing import Process, Value

###########################################################################################################
#
###########################################################################################################
class NetmodBase(  ):
   def __init__( self, log, config, parameters ):
      self.log     = log
      self.config  = config
      self.socket  = None
      self.parameters = parameters
      self.process  = None
      self.process_exit_flag       = Value('i')
      self.process_exit_flag.value = 0
      self.timestep = 0
      
      
   def start_module(self):
      process = Process( target = NetmodBase.work_wrapper, args=(self,) )
      process.daemon = True
      process.start()
      self.process = process
   
   def timetick(self):
      self.timestep = self.timestep + 1
      if self.timestep < 1:
         return True
      
      if self.process:
         if self.process_exit_flag.value > 0:
           self.terminate()
         if self.process.is_alive() == True:
           return True
         return False
      
      raise Exception("Process not created but time gone")
   
   def terminate(self):
      self.log.warning("Module %s received TERM!" % (self.__class__.__name__) )
      if self.process != None:
         if self.process_exit_flag.value < 10 :
            self.process_exit_flag.value = self.process_exit_flag.value + 1
         else :
            self.log.warning("Module %s did not quit peacefully!" % (self.__class__.__name__) )
            self.process.terminate()
            self.process = None
      
   def send_error( self, message ):
      self.log.error("Error on module %s : %s " % (self.__class__.__name__, message ) )
      self.send_message( "ERROR: " + message )
      
   def send_message(self, message ):
      message =  "%s: %s" % (self.__class__.__name__, message )
      self.socket.send( message )
       
   def work_wrapper(self):
     context = zmq.Context(1)
     
     module_socket = context.socket(zmq.PUB) # Output socket
     module_socket.connect( "%s:%s" % (self.config["protocol"], self.config["port_module_sub"]) )
     self.socket = module_socket  
     self.work()

   def work( self ):
      raise Exception("Base module work called")
   def term( self ):
      raise Exception("Base module work called")