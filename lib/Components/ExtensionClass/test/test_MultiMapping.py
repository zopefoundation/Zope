##############################################################################
#
# Copyright (c) 1996-2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
from MultiMapping import *

def sortprint(L):
    L.sort()
    print L

m=MultiMapping()

m.push({'spam':1, 'eggs':2})

print m['spam']
print m['eggs']

m.push({'spam':3})

print m['spam']
print m['eggs']

sortprint(m.pop().items())
sortprint(m.pop().items())

try:
    print m.pop()
    raise "That\'s odd", "This last pop should have failed!"
except: # I should probably raise a specific error in this case.
    pass
