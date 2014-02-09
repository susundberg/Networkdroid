

import NetmodBase
import subprocess
import re
import time

class Command( NetmodBase.NetmodBase ):
   
   def work_command( self, target_command ):
       
      self.log.info("Command ''%s' started " % ",".join( target_command)  )
      # Note: This surely leaves space for bad input, but as well the command could be 'rm -rf /'.
      process = subprocess.Popen( target_command , stdout=subprocess.PIPE )
      
      while True:
        time.sleep(1.0)
        process_state = process.poll()
         
        if process_state == None:
           # Still running
           self.send_message( "HB" )
           continue
        
        if process_state < 0:
            # Terminated by signal
            self.send_error("Terminated by signal: %d " % process_state )
            return False
        if process_state != 0:
           self.send_error("Nonzero exit: %d " % process_state )
           return False
        
        self.send_message( "TERM" )
        return True


class Ssh( Command ):
   def work( self ):
      target_command = self.config["command_ssh"].split(" ")
      return self.work_command( target_command  )
   