##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Placeless setup

$Id: __init__.py 30566 2005-05-30 22:37:34Z shh $
"""

from zope.app.tests.placelesssetup import setUp, tearDown

# For convenience
from Products.Five import zcml


def callZCML(zcml_callback):
    if callable(zcml_callback):
        zcml_callback()
    else:
        for func in zcml_callback:
            func()


def temporaryPlacelessSetUp(orig_func, placeless_available=True, required_zcml=[]):
    '''A wrapper for test functions that require CA to be available and/or
       some ZCML to be run during test fixture creation.
    '''
    if not placeless_available:
        return orig_func

    def wrapper(*args, **kw):
        __doc__ = '''%s ::

        @param required_zcml callback or iterable of callbacks
        required for setup of configuration needed by fixture
        creation.
        ''' % orig_func.__doc__

        # Setup the placeless stuff that's needed to create a fixture
        setUp()

        # Call any necessary callbacks for setting up ZCML
        callZCML(required_zcml)
        if kw.has_key('required_zcml'):
            zcml = kw.pop('required_zcml')
            callZCML(zcml)

        value = orig_func(*args, **kw)

        # And tear it down
        tearDown()
        return value

    return wrapper

