
import iclass, Util

Interface=Util.impliedInterface(
    iclass.Interface, "Interface",
    """Interface of Interface objects
    """)
iclass.Interface.__implements__=Interface

from iclass import Named, Class

from Basic import *

Util.assertTypeImplements(iclass.ClassType, Class)

from Number import *
from Mapping import *

del iclass # cruft
del Util   # cruft
