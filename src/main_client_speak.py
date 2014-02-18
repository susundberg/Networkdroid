
import json
import argparse
import sys
import zmq
import datetime

from Sundberg.Logger import *

from subprocess import call

def get_command_line_arguments( ):
   parser = argparse.ArgumentParser(description='Speak-aloud espeak client')
   parser.add_argument("configfile", help = "Set configuration file to be used")
   return parser.parse_args()

def main( args ):
   
   log = Logger("client_speak.log")
   log.info("Using configuration file: '%s'" % args.configfile )
   
   with open( args.configfile ) as fid:
      config = json.loads( fid.read() )

   # Handle the module print messages
   client = SpeakClient( config, log )
   client.mainloop()
   
   
class SpeakClient:
  def __init__(self, config, log ):
     self.module_alives = {}
     self.speak_lines   = {
                     "pingalive" : "Connection to droid server",
                     "pingip"    : "Connection to internet",
                     "pinghost"  : "Domain name server",
                     "ssh"       : "Nat compromised" 
                     }
     
     self.timeout = int( config["client_speak_timeout"] )
     self.address = config["protocol"] + ":" + config["port_client_pub"]
     self.log     = log
     self.speak_command = config["client_speak_cmd"]
     
  def mainloop(self):
     context = zmq.Context(1)
     receive_socket = context.socket(zmq.SUB)
     receive_socket.connect( self.address )
     receive_socket.setsockopt(zmq.SUBSCRIBE, "")
     receive_socket.setsockopt(zmq.RCVTIMEO, self.timeout )
   
     deadline = datetime.timedelta( milliseconds =  self.timeout )
   
     while( True ):
       # We need to first check if we have messages waiting, if yes, process those
       # If not, do dead module check and enter timeout receive
       # We need to do this to avoid a) dead modules check omitted b) dead modules check done while we have lines
       # waiting to be processed (since the speak can take several secs)
       
       # First check if we have messages waiting
       try:
         message = receive_socket.recv( flags = zmq.NOBLOCK )
         self.process_message( message )
         continue
       except zmq.ZMQError as error:
         if error.errno != zmq.EAGAIN :
            raise( error )
            
       self.check_for_dead_modules( deadline )     
       # No messages ready, do timeout receive
       try:
          message = receive_socket.recv(  )
          self.process_message( message )
       except zmq.ZMQError as error:
         if error.errno != zmq.EAGAIN :
            raise( error )
            
      
   
   
  def process_message( self, message ): 
      fields = message.split(":")
      if len(fields) == 2 and fields[1].strip() == "HB":
         module_name = fields[0].strip().lower()
         if module_name in self.speak_lines: 
            if module_name not in self.module_alives:
               self.speak_aloud( self.speak_lines[ module_name ] + " OK" )
               self.log.info("Module '%s' ONLINE" % module_name )
            self.module_alives[ module_name ] = datetime.datetime.now()
      else:
         print "GOT LINE:" + message
         
  def check_for_dead_modules(self, deadline ):       
     # Check for timeouted speak aloud 'connection dropped'
     current_time = datetime.datetime.now()
     to_remove = []
     for module_name in self.module_alives:
        elapsed_since_last_hb = current_time - self.module_alives[ module_name ]
        if elapsed_since_last_hb > deadline:
           self.speak_aloud( self.speak_lines[ module_name  ] + " got dropped")
           to_remove.append( module_name )
           self.log.info("Module '%s' went offline" % module_name )
     for module_name in to_remove:
           del self.module_alives[ module_name ]

  def speak_aloud( self, line ):
     retcode = call( [ self.speak_command, line ] )
     if retcode != 0 :
        self.log.error("Call '%s' returned nonzero: %d" % ( self.speak_command, retcode ) )
     self.log.debug("Speak aloud: " + line )

  
if __name__ == "__main__":
    sys.exit( main( get_command_line_arguments() ) )
  
  
  
  
