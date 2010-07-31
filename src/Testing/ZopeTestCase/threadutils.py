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
"""Parts of ZServer support are in this module so they can
be imported more selectively.
"""

from threading import Thread
from StringIO import StringIO

dummyLOG = StringIO()


def setNumberOfThreads(number_of_threads):
    '''Sets number of ZServer threads.'''
    try:
        from ZServer.PubCore import setNumberOfThreads
        setNumberOfThreads(number_of_threads)
    except ImportError:
        pass


def zserverRunner(host, port, log=None):
    '''Runs an HTTP ZServer on host:port.'''
    from ZServer import logger, asyncore
    from ZServer import zhttp_server, zhttp_handler
    if log is None: log = dummyLOG
    lg = logger.file_logger(log)
    hs = zhttp_server(ip=host, port=port, resolver=None, logger_object=lg)
    zh = zhttp_handler(module='Zope2', uri_base='')
    hs.install_handler(zh)
    asyncore.loop()


class QuietThread(Thread):
    '''This thread eats all exceptions'''
    def __init__(self, target=None, args=(), kwargs={}):
        Thread.__init__(self, target=target, args=args, kwargs=kwargs)
        self.__old_bootstrap = Thread._Thread__bootstrap
    def __bootstrap(self):
        try: self.__old_bootstrap(self)
        except: pass
    _Thread__bootstrap = __bootstrap


def QuietPublisher(self, accept):
    '''This server eats all exceptions'''
    try: self.__old_init__(accept)
    except: pass


from ZServer.PubCore.ZServerPublisher import ZServerPublisher
if not hasattr(ZServerPublisher, '__old_init__'):
    ZServerPublisher.__old_init__ = ZServerPublisher.__init__
    ZServerPublisher.__init__ = QuietPublisher

