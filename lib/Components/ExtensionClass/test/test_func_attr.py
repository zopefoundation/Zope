#! /usr/bin/env python
"""Test function attributes
   Jim Fulton
"""

verbose=1
from ExtensionClass import Base

def f(a): return a*a

class C(Base):
    def m(self, a): return a*a
    m.spam='eggs'

i=C()

if verbose: print 'Trying function wo attributes'
if f(2) != 4: print 'failed'

if verbose: print 'Trying method wo attributes'
if i.m(2) != 4: print 'failed'

if verbose: print 'Trying setting function attribute'
f.spam='eggs'

if verbose: print 'Trying function w attributes'
if f(2) != 4: print 'failed'

if verbose: print 'Trying method w attributes'
if i.m(2) != 4: print 'failed'

if verbose: print 'Trying method getattr'
try:
    if i.m.spam != 'eggs': print 'failed'
except AttributeError: print 'failed'
try:
    i.m.foo
    print 'failed'
except AttributeError: pass
