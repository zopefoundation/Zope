
from ZPublisher import publish_module
from cStringIO import StringIO

class ZServerPublisher:
    def __init__(self, name, accept):
       while 1:
           input, output, environ = accept()
           try:
               publish_module(
                   name, 
                   stdin=input,
                   stdout=output,
                   stderr=StringIO(), # whatever ;)
                   environ=environ)
           finally:
               output.close()
