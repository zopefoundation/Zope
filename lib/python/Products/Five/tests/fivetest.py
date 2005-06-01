##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Five test fixtures.

$Id: fivetest.py 12915 2005-05-31 10:23:19Z philikon $
"""
# ZopeTestCase was not designed to run tests as part of the
# Zope test suite proper. In particular, it intercepts product
# installation. We have to work around this for the Five tests
# by starting up Zope2 before doing anything else.
#
# Note: fivetest must be imported first thing by test modules!

def _part_of_zope_suite():
    # Find out if we run from softwarehome
    from os.path import normcase, realpath
    from App.config import getConfiguration
    softwarehome = normcase(realpath(getConfiguration().softwarehome))
    return normcase(realpath(__file__)).startswith(softwarehome)

def _start_zope():
    # Startup Zope 2.7 or 2.8+
    import Testing
    try:
        import Zope2 as Zope
    except ImportError:
        import Zope
    Zope.startup()

def _load_test_config():
    # Load up the ZCML config for the FiveTest product
    from os.path import dirname, join
    from Products.Five import zcml
    from Products.Five.tests.products import FiveTest
    prefix = dirname(FiveTest.__file__)
    zcml.load_config(join(prefix, 'testing.zcml'), FiveTest)

def _main():
    if _part_of_zope_suite():
        _start_zope()
    else:
        from Testing.ZopeTestCase import installProduct
        installProduct('Five')
        installProduct('PythonScripts')
    _load_test_config()

_main()


from Testing.ZopeTestCase import *

class FiveTestCase(ZopeTestCase):
    pass

