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
"""Support for ZODB sandboxes in ZTC

$Id$
"""

import ZopeLite as Zope2
import transaction
import base
import utils
import connections


class Sandboxed:
    '''Derive from this class and an xTestCase to make each test
       run in its own ZODB sandbox::

           class MyTest(Sandboxed, ZopeTestCase):
               ...
    '''

    def _app(self):
        '''Returns the app object for a test.'''
        app = Zope2.app(Zope2.sandbox().open())
        AppZapper().set(app)
        app = utils.makerequest(app)
        connections.register(app)
        return app

    def _close(self):
        '''Clears the transaction and the AppZapper.'''
        AppZapper().clear()
        transaction.abort()
        connections.closeAll()


class AppZapper:
    '''Application object share point'''

    __shared_state = {'_app': None}

    def __init__(self):
        self.__dict__ = self.__shared_state

    def set(self, app):
        self._app = app

    def clear(self):
        self._app = None

    def app(self):
        return self._app


def __bobo_traverse__(self, REQUEST=None, name=None):
    '''Makes ZPublisher.publish() use the current app object.'''
    app = AppZapper().app()
    if app is not None:
        return app
    return self.__old_bobo_traverse__(REQUEST, name)


from App.ZApplication import ZApplicationWrapper
if not hasattr(ZApplicationWrapper, '__old_bobo_traverse__'):
    ZApplicationWrapper.__old_bobo_traverse__ = (
        ZApplicationWrapper.__bobo_traverse__)
    ZApplicationWrapper.__bobo_traverse__ = __bobo_traverse__

