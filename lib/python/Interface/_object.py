##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
# 
##############################################################################
"""Provide a halfway believable rendition of Python 2.2's object

$Id: _object.py,v 1.2 2002/06/07 17:18:29 jim Exp $
"""

class _x:
    def m(self):
        pass

ClassTypes  = (type(_x), )
MethodTypes = (type(_x.m), )

isInstance = isinstance

try:
    object
    
except NameError:
    # Python 2.1
    
    try:
        from ExtensionClass import Base as object
    except ImportError:
        
        # Python 2.1 wo ExtensionClass
        class object: pass

    else:

        # Python 2.1 w ExtensionClass

        def isInstance(ob, klass):
            if type(type(ob)) is type(klass):
                return isinstance(ob, klass)
            return 0

        class _x(object):
            def m(self): pass

        ClassTypes  += (type(_x), )
        MethodTypes += (type(_x.m), )            

else:
    # Python 2.2
    ClassTypes += (type, )
    object = object
    isinstance = isinstance


