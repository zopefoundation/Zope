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
"""Utility functions

These functions are designed to be imported and run at
module level to add functionality to the test environment.
"""

import os
import sys
import time
import random
import transaction
import layer


@layer.appcall
def setupCoreSessions(app):
    '''Sets up the session_data_manager e.a.'''
    from Acquisition import aq_base
    commit = 0

    if not hasattr(app, 'temp_folder'):
        from Products.TemporaryFolder.TemporaryFolder import MountedTemporaryFolder
        tf = MountedTemporaryFolder('temp_folder', 'Temporary Folder')
        app._setObject('temp_folder', tf)
        commit = 1

    if not hasattr(aq_base(app.temp_folder), 'session_data'):
        from Products.Transience.Transience import TransientObjectContainer
        toc = TransientObjectContainer('session_data',
                    'Session Data Container',
                    timeout_mins=3,
                    limit=100)
        app.temp_folder._setObject('session_data', toc)
        commit = 1

    if not hasattr(app, 'browser_id_manager'):
        from Products.Sessions.BrowserIdManager import BrowserIdManager
        bid = BrowserIdManager('browser_id_manager',
                    'Browser Id Manager')
        app._setObject('browser_id_manager', bid)
        commit = 1

    if not hasattr(app, 'session_data_manager'):
        from Products.Sessions.SessionDataManager import SessionDataManager
        sdm = SessionDataManager('session_data_manager',
                    title='Session Data Manager',
                    path='/temp_folder/session_data',
                    requestName='SESSION')
        app._setObject('session_data_manager', sdm)
        commit = 1

    if commit:
        transaction.commit()


@layer.appcall
def setupSiteErrorLog(app):
    '''Sets up the error_log object required by ZPublisher.'''
    if not hasattr(app, 'error_log'):
        try:
            from Products.SiteErrorLog.SiteErrorLog import SiteErrorLog
        except ImportError:
            pass
        else:
            app._setObject('error_log', SiteErrorLog())
            transaction.commit()


def importObjectFromFile(container, filename, quiet=0):
    '''Imports an object from a (.zexp) file into the given container.'''
    from ZopeLite import _print, _patched
    quiet = quiet or not _patched
    start = time.time()
    if not quiet: _print("Importing %s ... " % os.path.basename(filename))
    container._importObjectFromFile(filename, verify=0)
    transaction.commit()
    if not quiet: _print('done (%.3fs)\n' % (time.time() - start))


_Z2HOST = None
_Z2PORT = None

def startZServer(number_of_threads=1, log=None):
    '''Starts an HTTP ZServer thread.'''
    global _Z2HOST, _Z2PORT
    if _Z2HOST is None:
        _Z2HOST = '127.0.0.1'
        _Z2PORT = random.choice(range(55000, 55500))
        from threadutils import setNumberOfThreads
        setNumberOfThreads(number_of_threads)
        from threadutils import QuietThread, zserverRunner
        t = QuietThread(target=zserverRunner, args=(_Z2HOST, _Z2PORT, log))
        t.setDaemon(1)
        t.start()
        time.sleep(0.1) # Sandor Palfy
    return _Z2HOST, _Z2PORT


def makerequest(app, stdout=sys.stdout):
    '''Wraps the app into a fresh REQUEST.'''
    from Testing.makerequest import makerequest as _makerequest
    environ = {}
    environ['SERVER_NAME'] = _Z2HOST or 'nohost'
    environ['SERVER_PORT'] = '%d' % (_Z2PORT or 80)
    environ['REQUEST_METHOD'] = 'GET'
    return _makerequest(app, stdout=stdout, environ=environ)


def appcall(func, *args, **kw):
    '''Calls a function passing 'app' as first argument.'''
    from base import app, close
    app = app()
    args = (app,) + args
    try:
        return func(*args, **kw)
    finally:
        transaction.abort()
        close(app)


def makelist(arg):
    '''Turns arg into a list. Where arg may be
       list, tuple, or string.
    '''
    if type(arg) == type([]):
        return arg
    if type(arg) == type(()):
        return list(arg)
    if type(arg) == type(''):
       return filter(None, [arg])
    raise ValueError('Argument must be list, tuple, or string')


__all__ = [
    'setupCoreSessions',
    'setupSiteErrorLog',
    'startZServer',
    'importObjectFromFile',
    'appcall',
    'makerequest',
    'makelist',
]

