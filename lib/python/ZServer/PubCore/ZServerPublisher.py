
from ZPublisher import publish_module
from cStringIO import StringIO

class ZServerPublisher:
    def __init__(self, accept):
       while 1:
           try:
               name,input,output,environ=accept()
               publish_module(
                   name, 
                   stdin=input,
                   stdout=output,
                   stderr=StringIO(), # whatever ;)
                   environ=environ)
           finally:
               output.close()
