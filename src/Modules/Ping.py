

import NetmodBase
import subprocess
import re
import time

class Ping( NetmodBase.NetmodBase ):
   def work( self ):
      if len( self.parameters ) != 1:
         self.send_error("Module has to have on parameter: host or ip to ping" )
         return False
      
      target_host = self.parameters[0]
      
      self.log.info("Ping module starting with target host '%s'" % target_host )
      
      process = subprocess.Popen( ['/bin/ping',target_host] , stdout=subprocess.PIPE )
      
      pattern = re.compile( r".*icmp_req=\d+ ttl=\d+ time=[\d\.]+")
      
      while True:
         message = process.stdout.readline()
         
         if message == "":
            self.log.debug("Received EOF")
            return
         
         message = message.strip()
         
         print "MESSAGE: '" + message + "'"
         
         if pattern.match( message ):
            self.send_message( "HB" )
         else:
            self.log.debug("Received unknown line: " + message )
            
         
   
   