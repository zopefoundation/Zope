
from iclass import Base

class Mutable(Base):
    """Mutable objects
    """

class Comparable(Base):
    """Objects that can be tested for equality
    """

class Orderable(Comparable):
    """Objects that can be compared with < > == <= >= !="""

class Hashable(Base):
    """Objects that support hash"""

class Key(Comparable, Hashable):
    """Objects that are immutable with respect to state that
    influences comparisons or hash values"""

    
    
