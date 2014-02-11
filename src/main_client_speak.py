
import json
import argparse
import sys
import zmq
import datetime

from Sundberg.Logger import *

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
     self.speak_lines   = { "PingAlive" : "Connection to server",
                     "PingIP"    : "Connection to internet" }
     self.timeout = int( config["client_speak_timeout"] )
     self.address = config["protocol"] + ":" + config["port_client_pub"]
     self.log     = log
     
  def mainloop(self):
     context = zmq.Context(1)
     receive_socket = context.socket(zmq.SUB)
     receive_socket.connect( self.address )
     receive_socket.setsockopt(zmq.SUBSCRIBE, "")
     receive_socket.setsockopt(zmq.RCVTIMEO, self.timeout )
   
     deadline = datetime.timedelta( milliseconds =  self.timeout )
   
     while( True ):
       self.check_for_dead_modules( deadline )
       try:
         message = receive_socket.recv(  )
       except zmq.ZMQError as error:
         if error.errno == zmq.EAGAIN :
            # Timeouted, check for dead modules and continue
            continue
         else :
            raise( error )
      
       self.process_message( message )
   
   
  def process_message( self, message ): 
      fields = message.split(":")
      if len(fields) == 2 and fields[1].strip() == "HB":
         module_name = fields[0].strip()
         if module_name in self.speak_lines: 
            if module_name not in self.module_alives:
               speak_aloud( self.speak_lines[ module_name ] + " OK" )
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
           speak_aloud( self.speak_lines[ module_name  ] + " got dropped")
           to_remove.append( module_name )
           self.log.info("Module '%s' went offline" % module_name )
     for module_name in to_remove:
           del self.module_alives[ module_name ]

def speak_aloud( line ):
   print "ESPEAK: " + line
      
   



   
if __name__ == "__main__":
    sys.exit( main( get_command_line_arguments() ) )
  
  
  
  
