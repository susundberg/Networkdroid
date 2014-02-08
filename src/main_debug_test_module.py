from Modules import Ping
import time

from Sundberg.Logger import *

log = Logger("test.log")

ping = Ping.Ping( log , { "protocol" : "tcp://127.0.0.1", "port_module_sub": "10000" }, ["google.com"] )

ping.start_module()


while True:
  print "DIED " + str(   ping.has_died() )
  time.sleep(1)

  
