##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
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
"""

from AccessControl.security import newInteraction
# For convenience
from Zope2.App import zcml  # NOQA
from zope.component.eventtesting import PlacelessSetup as EventPlacelessSetup
from zope.component.testing import PlacelessSetup as CAPlacelessSetup
from zope.container.testing import PlacelessSetup as ContainerPlacelessSetup
from zope.i18n.testing import PlacelessSetup as I18nPlacelessSetup
from zope.security.testing import addCheckerPublic


class PlacelessSetup(CAPlacelessSetup,
                     EventPlacelessSetup,
                     I18nPlacelessSetup,
                     ContainerPlacelessSetup):

    def setUp(self, doctesttest=None):
        CAPlacelessSetup.setUp(self)
        EventPlacelessSetup.setUp(self)
        ContainerPlacelessSetup.setUp(self)
        I18nPlacelessSetup.setUp(self)

        addCheckerPublic()
        newInteraction()


ps = PlacelessSetup()
setUp = ps.setUp


def tearDown():
    global ps
    tearDown_ = ps.tearDown

    def tearDown(doctesttest=None):
        tearDown_()
    return tearDown


tearDown = tearDown()

del ps


def callZCML(zcml_callback):
    if callable(zcml_callback):
        zcml_callback()
    else:
        for func in zcml_callback:
            func()


def temporaryPlacelessSetUp(orig_func, placeless_available=True,
                            required_zcml=[]):
    '''A wrapper for test functions that require CA to be available and/or
       some ZCML to be run during test fixture creation.
    '''
    if not placeless_available:
        return orig_func

    def wrapper(*args, **kw):
        '''%s ::

        @param required_zcml callback or iterable of callbacks
        required for setup of configuration needed by fixture
        creation.
        ''' % orig_func.__doc__

        # Setup the placeless stuff that's needed to create a fixture
        setUp()

        # Call any necessary callbacks for setting up ZCML
        callZCML(required_zcml)
        if 'required_zcml' in kw:
            req_zcml = kw.pop('required_zcml')
            callZCML(req_zcml)

        value = orig_func(*args, **kw)

        # And tear it down
        tearDown()
        return value

    return wrapper
