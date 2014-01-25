
import sys
import time


class Logger:
   
   def __init__(self, filename = None):
      self.fids = [ sys.stdout ] 
      if filename:
         self.fids.append( open( filename, 'w' ) )
      self.info( "Started at " + time.strftime("%X %x %Z") )
   
   def info( self, message ):
      self.output_raw("(II) " + message )
   def error( self, message ):
      self.output_raw("(EE) " + message )
   def warning( self, message ):
      self.output_raw("(WW) " + message )
   
   def output_raw( self, message ):
      for fid in self.fids:
         fid.write( message + "\n" )
         fid.flush()
      
   
      

      
   
   

