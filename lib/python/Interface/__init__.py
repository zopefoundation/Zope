
from Standard import Base

import iclass
new=iclass.Interface
del iclass

from Util import impliedInterface
from Util import assertTypeImplements, implementedBy, implementedByInstancesOf

from Attr import Attribute
from Method import Method

from Exceptions import BrokenImplementation

from pprint import interface_as_stx
from verify import verify_class_implementation
