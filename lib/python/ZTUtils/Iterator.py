##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
__doc__='''Iterator class

$Id: Iterator.py,v 1.3 2001/11/28 15:51:22 matt Exp $'''
__version__='$Revision: 1.3 $'[11:-2]

import string

class Iterator:
    '''Simple Iterator class'''

    __allow_access_to_unprotected_subobjects__ = 1
    
    def __init__(self, seq):
        self.seq = seq
        self.nextIndex = 0

    def next(self):
        i = self.nextIndex
        try:
            self.seq[i]
        except IndexError:
            return 0
        self.index = i
        self.nextIndex = i+1
        return 1

    def number(self): return self.nextIndex

    def even(self): return not self.index % 2

    def odd(self): return self.index % 2

    def letter(self, base=ord('a'), radix=26):
        index = self.index
        s = ''
        while 1:
            index, off = divmod(index, radix)
            s = chr(base + off) + s
            if not index: return s

    def Letter(self):
        return self.letter(base=ord('A'))

    def Roman(self, rnvalues=(
                    (1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),
                    (100,'C'),(90,'XC'),(50,'L'),(40,'XL'),
                    (10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')) ):
        n = self.index + 1
        s = ''
        for v, r in rnvalues:
            rct, n = divmod(n, v)
            s = s + r * rct
        return s

    def roman(self, lower=string.lower):
        return lower(self.Roman())

    def start(self): return self.nextIndex == 1

    def end(self):
        try: self.seq[self.nextIndex]
        except IndexError: return 1
        return 0

    def item(self):
        return self.seq[self.index]

    def length(self):
        return len(self.seq)

