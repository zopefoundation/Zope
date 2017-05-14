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

import os
import re
import sys

from ExtensionClass import Base


class Bruce(Base):
    __allow_access_to_unprotected_subobjects__ = 1
    isDocTemp = 0

    def __str__(self):
        return 'bruce'

    def __int__(self):
        return 42

    def __float__(self):
        return 42.0

    def keys(self):
        return ['bruce'] * 7

    def values(self):
        return [self] * 7

    def items(self):
        return [('bruce', self)] * 7

    def __len__(self):
        return 7

    def __getitem__(self, index):
        if (isinstance(index, int) and
                (index < 0 or index > 6)):
            raise IndexError(index)
        return self

    def __getattr__(self, name):
        if name[:1] == '_':
            raise AttributeError(name)
        return self

bruce = Bruce()


class arg(Base):
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, nn, aa):
        self.num, self.arg = nn, aa

    def __str__(self):
        return str(self.arg)


class argv(Base):
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, argv=sys.argv[1:]):
        args = self.args = []
        for aa in argv:
            args.append(arg(len(args) + 1, aa))

    def items(self):
        return [('spam%d' % a.num, a) for a in self.args]

    def values(self):
        return self.args

    def getPhysicalRoot(self):
        return self


def check_html(s1, s2):
    s1 = normalize_html(s1)
    s2 = normalize_html(s2)
    assert s1 == s2


def check_xml(s1, s2):
    s1 = normalize_xml(s1)
    s2 = normalize_xml(s2)
    assert s1 == s2, "XML Output Changed"


def normalize_html(s):
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"/>", ">", s)
    return s


def normalize_xml(s):
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"(?s)\s+<", "<", s)
    s = re.sub(r"(?s)>\s+", ">", s)
    return s


HERE = os.path.dirname(__file__)
input_dir = os.path.join(HERE, 'input')
output_dir = os.path.join(HERE, 'output')


def read_input(filename):
    filename = os.path.join(input_dir, filename)
    with open(filename, 'r') as fd:
        data = fd.read()
    return data


def read_output(filename):
    filename = os.path.join(output_dir, filename)
    with open(filename, 'r') as fd:
        data = fd.read()
    return data
