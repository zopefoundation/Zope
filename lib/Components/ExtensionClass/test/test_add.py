
from ExtensionClass import *

class foo(Base):

    def __add__(self,other): print 'add called'


foo()+foo()
