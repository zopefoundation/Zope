import warnings
warnings.warn("""\
The Interface.iclass module is no more. 
This is a stub module to allow ZClasses that subclass ObjectManager 
to continue to function - please fix your ZClasses (using the 'Subobjects' 
tab)""", 
DeprecationWarning)
# Old interface object. Provided for backwards compatibility - allows ZClasses
# that subclass ObjectManager to be used in 2.6.
class Interface:
    def __init__(self, *args, **kwargs):
       pass

