from zope.interface import classImplements

from _Acquisition import *
from interfaces import IAcquirer
from interfaces import IAcquisitionWrapper

classImplements(Explicit, IAcquirer)
classImplements(ExplicitAcquisitionWrapper, IAcquisitionWrapper)
classImplements(Implicit, IAcquirer)
classImplements(ImplicitAcquisitionWrapper, IAcquisitionWrapper)
