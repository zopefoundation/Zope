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
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__='''Examples from the Acquisition Algebra Presentation


$Id: test_AqAlg.py,v 1.6 2003/05/09 21:57:10 jeremy Exp $'''
__version__='$Revision: 1.6 $'[11:-2]

import Acquisition

import sys

def uid(obj, uids={}):
    uid = uids.get(id(obj))
    if uid is None:
        uid = uids[id(obj)] = len(uids) + 1
    return uid

def pretty(self, indent=0):
    context=getattr(self, 'aq_parent', None)
    if context is None: return self.__name__
    return "\n%s(%s \n%sof %s\n%s)" % (
        '  '*indent,
        pretty(self.aq_self, indent+1),
        '  '*indent,
        pretty(context, indent+1),
        '  '*indent,
        )

class I(Acquisition.Implicit):

    def __init__(self, name):
        self.__name__=name

    def __str__(self):
        context=getattr(self, 'aq_parent', None)
        if context is None: return self.__name__
        return "(%s: %s of %s)" % (uid(self), self.aq_self, context)

    __repr__=__str__

A=I('A')
A.B=I('B')
A.B.color='red'
A.C=I('C')
A.C.D=I('D')

def show(s, globals=globals()):
    print s, '-->', eval(s, globals)

def main():
    show('A')
    show('Acquisition.aq_chain(A)')
    show('Acquisition.aq_chain(A, 1)')
    show('map(Acquisition.aq_base, Acquisition.aq_chain(A, 1))')
    print

    show('A.C')
    show('Acquisition.aq_chain(A.C)')
    show('Acquisition.aq_chain(A.C, 1)')
    show('map(Acquisition.aq_base, Acquisition.aq_chain(A.C, 1))')
    print

    show('A.C.D')
    show('Acquisition.aq_chain(A.C.D)')
    show('Acquisition.aq_chain(A.C.D, 1)')
    show('map(Acquisition.aq_base, Acquisition.aq_chain(A.C.D, 1))')
    print

    show('A.B.C')
    show('Acquisition.aq_chain(A.B.C)')
    show('Acquisition.aq_chain(A.B.C, 1)')
    show('map(Acquisition.aq_base, Acquisition.aq_chain(A.B.C, 1))')
    print

    show('A.B.C.D')
    show('Acquisition.aq_chain(A.B.C.D)')
    show('Acquisition.aq_chain(A.B.C.D, 1)')
    show('map(Acquisition.aq_base, Acquisition.aq_chain(A.B.C.D, 1))')
    print

    show('A.B.C.D.color')
    show('Acquisition.aq_get(A.B.C.D, "color", None)')
    show('Acquisition.aq_get(A.B.C.D, "color", None, 1)')


if __name__=='__main__':
    main()
