


import json
import argparse
import sys
import zmq
from  multiprocessing import Process

from Sundberg.Logger import *
import Modules.BasePing


def get_command_line_arguments( ):
   parser = argparse.ArgumentParser(description='Server for Networkdroid')
   parser.add_argument("configfile", help = "Set configuration file to be used")
   parser.add_argument("--logfile" , help = "Set logfile to be used", default="server.log")
   return parser.parse_args()

def main( args ):
   log = Logger("server.log")
   log.info("Using configuration file: '%s'" % args.configfile )
   with open( args.configfile ) as fid:
      config = json.loads( fid.read() )
   
   server = Server( log, config )     
   
   # Then start the forward process, it will handle all messages
   # from modules to all the clients
   server.forward_modules_to_clients()
   log.info("Forwarder started")
   server.handle_client_requests()
      
   log.info("All done, bye")
   
   server.shutdown()
   
   return 0






###########################################################################################################
#
###########################################################################################################
class Server:
 def __init__( self, log, config ):
    self.log    = log
    self.config = config
    try:
      self.port_client_req = int( config["port_client_req"] )
      self.port_client_pub = int( config["port_client_pub"] )
      self.port_module_sub = int( config["port_module_sub"] )
    except KeyError as ke:
      self.log.error("Key %s is missing from configuration file" % str(ke) )
      raise Exception("Bad configuration")
      
    self.context = zmq.Context(1)
    self.protocol = config["protocol"]
    
    self.running_modules    = {}
    self.registered_modules = { 'baseping' : Modules.BasePing.BasePing }
    
 def shutdown( self ):
    self.log.warning("Server shutdown started.")
    self.forward_process.terminate()
    self.context.term()
    self.log.info("Server shutdown done.")
 
 ###########################################################################################################
 def forward_modules_to_clients( self ):
    self.forward_process = Process( target = Server.forward_modules_to_clients_raw,
                         args = ( self,  ) )
    self.forward_process.daemon = True
    self.forward_process.start()
    
 def forward_modules_to_clients_raw( self ):     
    self.log.info("Starting SUB->PUB forward from socket %d to %d " % (self.port_module_sub, self.port_client_pub ))
    #import pdb; pdb.set_trace()
    frontend = None
    backend = None
    try:
      # Socket facing clients
      context = zmq.Context(1)
      frontend = context.socket(zmq.SUB)
      frontend.bind("%s:%d" % ( self.protocol, self.port_module_sub ) )
      # No filtering of messages please
      frontend.setsockopt(zmq.SUBSCRIBE, "")
      
      # Socket facing services
      backend = context.socket(zmq.PUB)
      backend.bind("%s:%d" % ( self.protocol, self.port_client_pub  ) )

      zmq.device( zmq.FORWARDER, frontend, backend )
      print "FAIL" 
    except Exception as e:
       self.log.error("Exception while running forward: " + str(e))
       raise Exception("Forwarder failed")
    
    finally:
        pass
        if frontend: 
           frontend.close()
        if backend:
           backend.close()
           
 ###########################################################################################################
    
 def handle_client_requests( self ):
    
    socket = self.context.socket( zmq.REP )
    socket.bind("%s:%d" % ( self.protocol, self.port_client_req ) )
    
    self.log.info("Starting control socket to port %d " % self.port_client_req  )
     
    commands_to_functions_map = { 'launch' : self.module_launch,
                                  'kill'   : self.module_kill
                                }
    while True:
      message = socket.recv().lower()
      
      if message == "term":
         break
         
      if message == "list":
         socket.send("MODULES " + " ".join( self.registered_modules.keys() ) )
         continue
      
      parts=message.split()
      
      if len(parts) != 2 or parts[0] not in commands_to_functions_map:
         self.log.warning("Not sure what we received: " + message )
         socket.send("FAIL")
         continue
      
      if commands_to_functions_map[ parts[0] ]( parts[1] ):
        socket.send("OK")
      else:
        socket.send("FAIL")
        
 ###########################################################################################################     
 def module_launch(self, module_name ):
     if module_name not in self.registered_modules:
        self.log.warning("Module '%s' is not known, cannot be launched." % module_name )
        return False
     
     if module_name in self.running_modules:
        self.log.warning("Module '%s' is already running." % module_name )
        return False;
     
     self.log.info("Launching module '%s'." % module_name )
     module = self.registered_modules[module_name]( self.log, self.config ) 
     
     if module.start_module() == False:
        return False
     
     self.running_modules[ module_name ] = module
     return True
  
  
 def module_kill( self, module_name ):
     if module_name not in self.running_modules:
        self.log.warning("Module '%s' kill requested but its not running!" % module_name )
        return False
     
     self.running_modules[ module_name ].terminate()
     del( self.running_modules[ module_name ] )
     self.log.info("Killing module '%s'." % module_name )
     return True
   
   



   
if __name__ == "__main__":
    sys.exit( main( get_command_line_arguments() ) )
  