##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

from Exceptions import BrokenImplementation, DoesNotImplement
from Exceptions import BrokenMethodImplementation
from types import FunctionType
from Method import fromMethod, fromFunction
from _object import MethodTypes

def _verify(iface, candidate, tentative=0, vtype=None):
    """

    Verify that 'candidate' might correctly implements 'iface'.
    This involves:

      o Making sure the candidate defines all the necessary methods

      o Making sure the methods have the correct signature

      o Making sure the candidate asserts that it implements the interface

    Note that this isn't the same as verifying that the class does
    implement the interface.

    If optional tentative is true, suppress the "is implemented by" test.
    """

    if vtype is 'c':
        tester = iface.isImplementedByInstancesOf
    else:
        tester = iface.isImplementedBy

    if not tentative and not tester( candidate ):
        raise DoesNotImplement(iface)

    for n, d in iface.namesAndDescriptions(1):
        if not hasattr(candidate, n):
            raise BrokenImplementation(iface, n)

        attr = getattr(candidate, n)
        if type(attr) is FunctionType:
            # should never get here
            meth = fromFunction(attr, n)
        elif type(attr) in MethodTypes:
            meth = fromMethod(attr, n)
        else:
            continue # must be an attribute...

        d=d.getSignatureInfo()
        meth = meth.getSignatureInfo()

        mess = _incompat(d, meth)
        if mess:
            raise BrokenMethodImplementation(n, mess)

    return 1

def verifyClass(iface, candidate, tentative=0):
    return _verify(iface, candidate, tentative, vtype='c')

def verifyObject(iface, candidate, tentative=0):
    return _verify(iface, candidate, tentative, vtype='o')

def _incompat(required, implemented):
    #if (required['positional'] !=
    #    implemented['positional'][:len(required['positional'])]
    #    and implemented['kwargs'] is None):
    #    return 'imlementation has different argument names'
    if len(implemented['required']) > len(required['required']):
        return 'implementation requires too many arguments'
    if ((len(implemented['positional']) < len(required['positional']))
        and not implemented['varargs']):
        return "implementation doesn't allow enough arguments"
    if required['kwargs'] and not implemented['kwargs']:
        return "implementation doesn't support keyword arguments"
    if required['varargs'] and not implemented['varargs']:
        return "implementation doesn't support variable arguments"
