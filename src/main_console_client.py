
import json
import argparse
import sys
import zmq
from  multiprocessing import Process


def get_command_line_arguments( ):
   parser = argparse.ArgumentParser(description='Server for Networkdroid')
   parser.add_argument("configfile", help = "Set configuration file to be used")
   return parser.parse_args()

def main( args ):
   
   with open( args.configfile ) as fid:
      config = json.loads( fid.read() )

   context = zmq.Context(1)
   protocol = config["protocol"]
   
   # Handle the module print messages
   address = protocol + ":" + config["port_client_pub"]
   receive_process = Process( target = receive_thread, args=( address, ) )
   receive_process.start()
   print "Receive process running"
   
   # And then the real communication
   control_socket = context.socket( zmq.REQ )
   control_socket.connect( protocol + ":" + config["port_client_req"] )
   print "Starting console"
   
   while True:
      input_line = sys.stdin.readline().strip()
      
      if len(input_line) < 1:
         break
         
      print "S: " + input_line
      control_socket.send(input_line)
      print "R: " + control_socket.recv()
   

def receive_thread( address ):
   context = zmq.Context(1)
   receive_socket  = context.socket(zmq.SUB)
   receive_socket.connect( address )
   receive_socket.setsockopt(zmq.SUBSCRIBE, "")
   print "Receive socket here. Connect to " + address
   while( True ):
      message = receive_socket.recv()
      print "P: " + message
   
   
if __name__ == "__main__":
    sys.exit( main( get_command_line_arguments() ) )
  
  
  
  
