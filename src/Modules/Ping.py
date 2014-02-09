

import NetmodBase
import subprocess
import re
import time


class Ping( NetmodBase.NetmodBase ):
   def pingwork( self, target_host ):
      
      self.log.info("Ping module starting with target host '%s'" % target_host )
      
      process = subprocess.Popen( ['/bin/ping',target_host] , stdout=subprocess.PIPE )
      
      pattern = re.compile( r".*icmp_req=\d+ ttl=\d+ time=[\d\.]+")
      
      while True:
         message = process.stdout.readline()
         
         if message == "":
            self.log.debug("Received EOF")
            return
         message = message.strip()
         
         if pattern.match( message ):
            self.send_message( "HB" )
         else:
            self.log.debug("Received unknown line: " + message )

class PingAlive( NetmodBase.NetmodBase ):
   def work( self ):
      while True:
         self.send_message( "HB" )
         time.sleep(1.0)

class PingIP( Ping ):
   def work( self ):
      target_host = self.config["ping_ip"]
      return self.pingwork( target_host )

            
class PingHost( Ping ):
   def work( self ):
      target_host = self.config["ping_host"]
      return self.pingwork( target_host )

   