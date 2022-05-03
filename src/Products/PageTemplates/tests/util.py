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
import os.path
import re
import sys
import unittest

from ExtensionClass import Base
from Products.PageTemplates.engine import Program
from zope.component import provideUtility
from zope.pagetemplate.interfaces import IPageTemplateEngine
from zope.pagetemplate.pagetemplate import PageTemplateEngine


# Dummy TestCase to use the assertions outside the actual tests.
TEST_CASE = unittest.TestCase('__init__')


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
        if isinstance(index, int) and (index < 0 or index > 6):
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
    if not isinstance(s2, bytes) and isinstance(s1, bytes):
        # convert to common type
        s1 = s1.decode("utf-8")  # our encoding
    s1 = normalize_html(s1)
    s2 = normalize_html(s2)
    TEST_CASE.assertEqual(s1, s2)


def check_xml(s1, s2):
    s1 = normalize_xml(s1)
    s2 = normalize_xml(s2)
    TEST_CASE.assertEqual(s1, s2, "XML Output Changed")


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


def _open(filename, mode):
    # Define explicit encoding for windows platform
    return open(filename, mode, encoding='utf-8')


def read_input(filename):
    filename = os.path.join(input_dir, filename)
    with _open(filename, 'r') as fd:
        data = fd.read()
    return data


def read_output(filename):
    filename = os.path.join(output_dir, filename)
    with _open(filename, 'r') as fd:
        data = fd.read()
    return data


def exists_output(filename):
    filename = os.path.join(output_dir, filename)
    return os.path.exists(filename)


def useChameleonEngine():
    # Force the use of the new chameleon rendering engine (the new default).
    # Its use depends on a utility registration that is queried in
    # zope.pagetemplate,pagetemplate.PageTemplate's _cook method. Unfortunately
    # the fallback is the old Zope engine if there is no registration, so we
    # force one here for use by unit tests.
    provideUtility(Program, IPageTemplateEngine)


def useOldZopeEngine():
    # BBB Force the use of the old Zope page template engine, which is needed
    # for some tests that test features only supported by it.
    provideUtility(PageTemplateEngine, IPageTemplateEngine)
