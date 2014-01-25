


import json
import argparse
import sys
import zmq
from  multiprocessing import Process

from Sundberg.Logger import *

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
   time.sleep(5)
   log.info("All done, bye")
   
   server.shutdown()
   
   return 0


###############################################################################
#
###############################################################################
class Server:
 def __init__( self, log, config ):
    self.log   = log
    try:
      self.port_client_req = int( config["port_client_req"] )
      self.port_client_pub = int( config["port_client_pub"] )
      self.port_module_sub = int( config["port_module_sub"] )
    except KeyError as ke:
      self.log.error("Key %s is missing from configuration file" % str(ke) )
      raise Exception("Bad configuration")
      
    self.context = zmq.Context(1)
      
 def shutdown( self ):
    self.context.term()
    self.log.info("Server shutdown done.")
    
 def forward_modules_to_clients( self ):
    

    self.log.info("Starting SUB->PUB forward from socket %d to %d " % (self.port_module_sub, self.port_client_pub ))
    #import pdb; pdb.set_trace()
    frontend = None
    backend = None
    try:
      # Socket facing clients
      frontend = self.context.socket(zmq.SUB)
      frontend.bind("tcp://127.0.0.1:%d" % self.port_module_sub )
      # No filtering of messages please
      frontend.setsockopt(zmq.SUBSCRIBE, "")
      
      # Socket facing services
      backend = self.context.socket(zmq.PUB)
      backend.bind("tcp://127.0.0.1:%d" % self.port_client_pub  )
      
      process = Process( target = zmq.device,
                         args = ( zmq.FORWARDER, frontend, backend ) )
      process.daemon = True
      process.start()
        
    except Exception as e:
       self.log.error("Exception while running forward: " + str(e))
       raise Exception("Forwarder failed")
    
    finally:
        pass
        if frontend: 
           frontend.close()
        if backend:
           backend.close()
           
   
   
   
if __name__ == "__main__":
    sys.exit( main( get_command_line_arguments() ) )
  