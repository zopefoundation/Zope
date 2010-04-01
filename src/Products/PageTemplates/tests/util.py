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

######################################################################
# Utility facilities to aid setting things up.

import os, sys, string, re

from ExtensionClass import Base

class Bruce(Base):
    __allow_access_to_unprotected_subobjects__=1
    def __str__(self): return 'bruce'
    def __int__(self): return 42
    def __float__(self): return 42.0
    def keys(self): return ['bruce']*7
    def values(self): return [self]*7
    def items(self): return [('bruce',self)]*7
    def __len__(self): return 7
    def __getitem__(self,index):
        if (type(index) is type(1) and
            (index < 0 or index > 6)): raise IndexError, index
        return self
    isDocTemp=0
    def __getattr__(self,name):
        if name[:1]=='_': raise AttributeError, name
        return self

bruce=Bruce()

class arg(Base):
    __allow_access_to_unprotected_subobjects__=1
    def __init__(self,nn,aa): self.num, self.arg = nn, aa
    def __str__(self): return str(self.arg)

class argv(Base):
    __allow_access_to_unprotected_subobjects__=1
    def __init__(self, argv=sys.argv[1:]):
        args=self.args=[]
        for aa in argv:
            args.append(arg(len(args)+1,aa))

    def items(self):
        return map(lambda a: ('spam%d' % a.num, a), self.args)

    def values(self): return self.args

    def getPhysicalRoot(self):
        return self

def nicerange(lo, hi):
    if hi <= lo+1:
        return str(lo+1)
    else:
        return "%d,%d" % (lo+1, hi)

def check_html(s1, s2):
    s1 = normalize_html(s1)
    s2 = normalize_html(s2)
    if s1!=s2:
        print
        from OFS.ndiff import SequenceMatcher, dump, IS_LINE_JUNK
        a = string.split(s1, '\n')
        b = string.split(s2, '\n')
        def add_nl(s):
            return s + '\n'
        a = map(add_nl, a)
        b = map(add_nl, b)
        cruncher=SequenceMatcher(isjunk=IS_LINE_JUNK, a=a, b=b)
        for tag, alo, ahi, blo, bhi in cruncher.get_opcodes():
            if tag == 'equal':
                continue
            print nicerange(alo, ahi) + tag[0] + nicerange(blo, bhi)
            dump('<', a, alo, ahi)
            if a and b:
                print '---'
            dump('>', b, blo, bhi)
    assert s1==s2, "HTML Output Changed"

def check_xml(s1, s2):
    s1 = normalize_xml(s1)
    s2 = normalize_xml(s2)
    assert s1==s2, "XML Output Changed"

def normalize_html(s):
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"/>", ">", s)
    return s

def normalize_xml(s):
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"(?s)\s+<", "<", s)
    s = re.sub(r"(?s)>\s+", ">", s)
    return s


import Products.PageTemplates.tests
dir = os.path.dirname( Products.PageTemplates.tests.__file__)
input_dir = os.path.join(dir, 'input')
output_dir = os.path.join(dir, 'output')

def read_input(filename):
    filename = os.path.join(input_dir, filename)
    return open(filename, 'r').read()

def read_output(filename):
    filename = os.path.join(output_dir, filename)
    return open(filename, 'r').read()
