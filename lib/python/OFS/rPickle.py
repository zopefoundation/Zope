"""Restricted unpickler"""

__version__='$Revision: 1.2 $'[11:-2]


import pickle

reg={}

class Unpickler(pickle.Unpickler):
    def find_class(self, module, name):
	try:    return reg[(module,name)]
	except: raise SystemError, 'Class not registered'

    def load_string(self):
	raise 'BadPickle', 'Non binstring'

# Public interface

from cStringIO import StringIO

def loads(s):
    """Unpickle a string"""
    return Unpickler(StringIO(s)).load()

def register(mod, cls, obj):
    """Register a class"""
    reg[(mod,cls)]=obj

def unregister(mod, cls):
    """Unregister a class"""
    del reg[(mod,cls)]

    
