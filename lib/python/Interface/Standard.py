
import iclass, Util

Interface=Util.impliedInterface(
    iclass.Interface, "Interface",
    """Interface of Interface objects
    """)
iclass.Interface.__implements__=Interface

from Basic import *

class Class(Base):
    """Implement shared instance behavior and create instances
    
    Classes can be called to create an instance.  This interface does
    not specify what if any arguments are required.
    """

Util.assertTypeImplements(iclass.ClassType, Class)

from Number import *
from Mapping import *
