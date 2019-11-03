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
"""Support for ZODB sandboxes in ZTC
"""

import contextlib

import transaction
import ZPublisher.WSGIPublisher
from Testing.makerequest import makerequest
from Testing.ZopeTestCase import ZopeLite as Zope2
from Testing.ZopeTestCase import connections


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
        app = makerequest(app)
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


@contextlib.contextmanager
def load_app(module_info):
    """Let the Publisher use the current app object."""
    app = AppZapper().app()
    if app is not None:
        yield app, module_info[1], module_info[2]
    else:
        with ZPublisher.WSGIPublisher.__old_load_app__(module_info) as ret:
            yield ret


if not hasattr(ZPublisher.WSGIPublisher, '__old_load_app__'):
    ZPublisher.WSGIPublisher.__old_load_app__ = ZPublisher.WSGIPublisher.load_app  # NOQA: E501
    ZPublisher.WSGIPublisher.load_app = load_app
