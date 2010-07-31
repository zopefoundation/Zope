##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Restricted unpickler
"""

import pickle

reg={}

class Unpickler(pickle.Unpickler):
    def find_class(self, module, name):
        try:    return reg[(module,name)]
        except: raise SystemError, 'Class not registered'

    def load_string(self):
        raise pickle.UnpicklingError, 'Bad pickle: Non binstring'

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
