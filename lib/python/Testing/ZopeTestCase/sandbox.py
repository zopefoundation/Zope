#
# Support for ZODB sandboxes in ZTC
#

# $Id: sandbox.py,v 1.1 2004/01/09 15:03:04 shh42 Exp $

import ZopeLite as Zope
import utils


class Sandboxed:
    '''Derive from this class and an xTestCase to make each test
       run in its own ZODB sandbox::

           class MyTest(Sandboxed, ZopeTestCase):
               ...
    '''

    def _app(self):
        '''Returns the app object for a test.'''
        app = Zope.app(Zope.sandbox().open())
        AppZapper().set(app)
        return utils.makerequest(app)

    def _close(self):
        '''Clears the transaction and the AppZapper.'''
        get_transaction().abort()
        AppZapper().clear()


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


from ZODB.ZApplication import ZApplicationWrapper
ZApplicationWrapper.__old_bobo_traverse__ = ZApplicationWrapper.__bobo_traverse__
ZApplicationWrapper.__bobo_traverse__ = __bobo_traverse__

