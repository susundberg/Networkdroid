


import json
import argparse
import sys
import zmq
import time

from  multiprocessing import Process

from Sundberg.Logger import *
from Modules import NetmodBase, Ping, Command


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
   
   server.registered_modules = { 'heartbeat' : Ping.PingAlive,
                                 'ping_ip'   : Ping.PingIP,
                                 'ping_host' : Ping.PingHost,
                                 'ssh'       : Command.Ssh
                               }
   
   server.commands_to_functions_map = { 
                                 'launch' : Server.function_module_launch,
                                 'kill'   : Server.function_module_kill,
                                 'list'   : Server.function_print_info,
                                 'ping'   : function_ping_pong
                                }
   
   # Then start the forward process, it will handle all messages
   # from modules to all the clients
   server.forward_modules_to_clients()
   server.function_module_launch( ["heartbeat"] )
   
   log.info("Forwarder started")
   server.handle_client_requests()
      
   log.info("All done, bye")
   
   server.shutdown()
   
   return 0


def function_ping_pong( server, module_arguments ):
   return "PONG " + " ".join(module_arguments)


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
    self.registered_modules = None
    self.commands_to_functions_map = None
    
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
 # Main loop here
 ###########################################################################################################
 def handle_client_requests( self ):

    socket = self.context.socket( zmq.REP )
    socket.bind("%s:%d" % ( self.protocol, self.port_client_req ) )
    socket.setsockopt(zmq.RCVTIMEO, 1000 )
    self.log.info("Starting control socket to port %d " % self.port_client_req  )
    while True:
      self.check_for_died_modules()
      message = self.module_message_receive( socket )
      
      if message == None:
         continue
      
      if message == "term":
         break
         
      self.module_message_process( message, socket )
      
 ###########################################################################################################
 def check_for_died_modules( self ):
   # Check for modules that have died
   to_kill = []
   for module_name in self.running_modules:
      if self.running_modules[ module_name ].has_died() == True:
         to_kill.append( module_name )
   for module_name in to_kill:
      self.function_module_kill( [ module_name ] )
         
 ###########################################################################################################
 def module_message_receive(self, socket):
   try:
      message = socket.recv( )
   except zmq.ZMQError as error:
     if error.errno == zmq.EAGAIN :
        # Timeouted, check for dead modules and continue
      return None
     else :
      raise( error )
   return message.lower()

   
 def module_message_process( self, message, socket ):
   parts=message.split()
   
   if len(parts) < 1 or parts[0] not in self.commands_to_functions_map:
      self.log.warning("Not sure what we received: " + message )
      socket.send("FAIL")
      return True
   
   function_to_run = self.commands_to_functions_map[ parts[0] ]
   message = function_to_run ( self, parts[1:] )
   socket.send(message)
      

 def function_print_info( self, arguments ):
      return "MODULES " + " ".join( self.registered_modules.keys())
        
 ###########################################################################################################     

    
 def function_module_launch(self, module_arguments ):
     if len( module_arguments ) < 1:
        self.log.warning("Launch module called without parameters")
        return "FAIL"
     
     module_name = module_arguments[0]
     module_arguments = module_arguments[1:]
     
     if module_name not in self.registered_modules:
        self.log.warning("Module '%s' is not known, cannot be launched." % module_name )
        return "FAIL"
     
     if module_name in self.running_modules:
        self.log.warning("Module '%s' is already running." % module_name )
        return "FAIL"
     
     self.log.info("Launching module '%s' -- %s." % (module_name, ",".join(module_arguments) ) )
     try:
        module = self.registered_modules[module_name]( self.log, self.config, module_arguments ) 
     
        if module.start_module() == False:
           return "FAIL"
     except Exception as e:
        self.log.error("Module launch failed: " + str(e))
        return "FAIL"
     
     self.running_modules[ module_name ] = module
     return "OK"
  
  
 def function_module_kill( self, module_arguments ):
     print "GOT : " + str( module_arguments )
     if len( module_arguments ) != 1:
        self.log.warning("Module kill requested with bad parameters!")
        return "FAIL"
     
     module_name = module_arguments[0]   
     if module_name not in self.running_modules:
        self.log.warning("Module '%s' kill requested but its not running!" % module_name )
        return "FAIL"
     
     self.running_modules[ module_name ].terminate()
     del self.running_modules[ module_name ] 
     self.log.info("Killing module '%s'." % module_name )
     return "OK"
   
   

   
if __name__ == "__main__":
    sys.exit( main( get_command_line_arguments() ) )
  