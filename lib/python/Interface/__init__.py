
from Standard import Base

import iclass
new=iclass.Interface
InterfaceInterface=iclass.InterfaceInterface
# del iclass

from Util import impliedInterface
from Util import assertTypeImplements, objectImplements, instancesOfObjectImplements

from Attr import Attribute
from Method import Method

from Exceptions import BrokenImplementation

from pprint import interface_as_stx
from verify import verify_class_implementation
