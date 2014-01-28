import sys
import zmq


context = zmq.Context(1)
protocol = "tcp://127.0.0.1:7401"
   
   # Handle the module print messages
receive_socket  = context.socket(zmq.SUB)
receive_socket.connect( protocol )
receive_socket.setsockopt(zmq.SUBSCRIBE, "")

while True:
  print "GOT: " + receive_socket.recv()
