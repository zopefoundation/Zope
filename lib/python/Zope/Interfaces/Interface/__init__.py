
from Standard import Base

import iclass
new=iclass.Interface
del iclass

from Util import impliedInterface

Registered_Interfaces = {}

def Interface(klass, __name__=None, __doc__=None):
    """

    why are we doing this maddness?  to hook the interface
    registration.  This must die!

    """
    I = impliedInterface(klass, __name__, __doc__)
    Registered_Interfaces[I.__name__] = I
    return I
    


from Util import assertTypeImplements, implementedBy, implementedByInstancesOf

from Attr import Attribute
from Method import Method

from Exceptions import BrokenImplementation
