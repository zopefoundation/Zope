##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Method interfaces

Revision information:
$Id$
"""
import Exceptions
from Attribute import Attribute

sig_traits = ['positional', 'required', 'optional', 'varargs', 'kwargs']

CO_VARARGS = 4
CO_VARKEYWORDS = 8

class Method(Attribute):
    """Method interfaces

    The idea here is that you have objects that describe methods.
    This provides an opportunity for rich meta-data.
    """

    # We can't say this yet because we don't have enough
    # infrastructure in place.
    #
    #__implements__ = IMethod

    interface=''

    def __call__(self, *args, **kw):
        raise Exceptions.BrokenImplementation(self.interface, self.__name__)

    def getSignatureInfo(self):
        info = {}
        for t in sig_traits:
            info[t] = getattr(self, t)

        return info

    def getSignatureString(self):
        sig = "("
        for v in self.positional:
            sig = sig + v
            if v in self.optional.keys():
                sig = sig + "=%s" % `self.optional[v]`
            sig = sig + ", "
        if self.varargs:
            sig = sig + ("*%s, " % self.varargs)
        if self.kwargs:
            sig = sig + ("**%s, " % self.kwargs)

        # slice off the last comma and space
        if self.positional or self.varargs or self.kwargs:
            sig = sig[:-2]

        sig = sig + ")"
        return sig


def fromFunction(func, interface='', imlevel=0):
    m=Method(func.__name__, func.__doc__)
    defaults=func.func_defaults or ()
    c=func.func_code
    na=c.co_argcount-imlevel
    names=c.co_varnames[imlevel:]
    d={}
    nr=na-len(defaults)
    if nr < 0:
        defaults=defaults[-nr:]
        nr=0

    for i in range(len(defaults)):
        d[names[i+nr]]=defaults[i]

    m.positional=names[:na]
    m.required=names[:nr]
    m.optional=d

    argno = na
    if c.co_flags & CO_VARARGS:
        m.varargs = names[argno]
        argno = argno + 1
    else:
        m.varargs = None
    if c.co_flags & CO_VARKEYWORDS:
        m.kwargs = names[argno]
    else:
        m.kwargs = None

    m.interface=interface
    return m

def fromMethod(meth, interface=''):
    func = meth.im_func
    return fromFunction(func, interface, imlevel=1)
