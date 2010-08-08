##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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
""" Tests of the ZopeStarter class """

import cStringIO
import errno
import logging
import os
import random
import sys
import tempfile
import unittest

import ZConfig
from ZConfig.components.logger.tests import test_logger
from ZConfig.components.logger.loghandler import NullHandler

import Zope2.Startup
import Products

from App.config import getConfiguration, setConfiguration

TEMPNAME = tempfile.mktemp()
TEMPPRODUCTS = os.path.join(TEMPNAME, "Products")

def getSchema():
    startup = os.path.dirname(Zope2.Startup.__file__)
    schemafile = os.path.join(startup, 'zopeschema.xml')
    return ZConfig.loadSchema(schemafile)

# try to preserve logging state so we don't screw up other unit tests
# that come later

logger_states = {}
for name in (None, 'trace', 'access'):
    logger = logging.getLogger(name)
    logger_states[name] = {'level':logger.level,
                           'propagate':logger.propagate,
                           'handlers':logger.handlers,
                           'filters':logger.filters}

class ZopeStarterTestCase(test_logger.LoggingTestBase):

    schema = None

    def setUp(self):
        from ZConfig.components.logger import loghandler
        if self.schema is None:
            ZopeStarterTestCase.schema = getSchema()
        test_logger.LoggingTestBase.setUp(self)

    def tearDown(self):
        try:
            os.rmdir(TEMPPRODUCTS)
            os.rmdir(TEMPNAME)
        except:
            pass
        Products.__path__ = [d for d in Products.__path__
                             if os.path.exists(d)]

        test_logger.LoggingTestBase.tearDown(self)

        # reset logger states
        for name in (None, 'access', 'trace'):
            logger = logging.getLogger(name)
            logger.__dict__.update(logger_states[name])

    def _clearHandlers(self):
        from ZConfig.components.logger import loghandler
        del loghandler._reopenable_handlers[:]

    def get_starter(self, conf):
        starter = Zope2.Startup.get_starter()
        starter.setConfiguration(conf)
        return starter

    def load_config_text(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        schema = self.schema
        sio = cStringIO.StringIO(
            text.replace("<<INSTANCE_HOME>>", TEMPNAME))
        try:
            os.mkdir(TEMPNAME)
            os.mkdir(TEMPPRODUCTS)
        except OSError, why:
            if why == 17:
                # already exists
                pass
        conf, self.handler = ZConfig.loadConfigFile(schema, sio)
        self.assertEqual(conf.instancehome, TEMPNAME)
        return conf

    def testSetupLocale(self):
        # XXX this almost certainly won't work on all systems
        import locale
        try:
            try:
                conf = self.load_config_text("""
                    instancehome <<INSTANCE_HOME>>
                    locale en_GB""")
            except ZConfig.DataConversionError, e:
                # Skip this test if we don't have support.
                if e.message.startswith(
                    'The specified locale "en_GB" is not supported'):
                    return
                raise
            starter = self.get_starter(conf)
            starter.setupLocale()
            self.assertEqual(tuple(locale.getlocale()), ('en_GB', 'ISO8859-1'))
        finally:
            # reset to system-defined locale
            locale.setlocale(locale.LC_ALL, '')

    def testSetupStartupHandler(self):
        if sys.platform[:3].lower() == "win":
            return
        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>
            debug-mode on
            <eventlog>
             level info
             <logfile>
               path <<INSTANCE_HOME>>/event.log
              level info
             </logfile>
             <logfile>
               path <<INSTANCE_HOME>>/event2.log
              level blather
             </logfile>
           </eventlog>""")
        starter = self.get_starter(conf)
        starter.setupInitialLogging()

        # startup handler should take on the level of the event log handler
        # with the lowest level
        logger = starter.event_logger
        self.assertEqual(starter.startup_handler.level, 15) # 15 is BLATHER
        self.assert_(starter.startup_handler in logger.handlers)
        self.assertEqual(logger.level, 15)
        # We expect a debug handler and the startup handler:
        self.assertEqual(len(logger.handlers), 2)

        # XXX need to check that log messages get written to
        # sys.stderr, not that the stream identity for the startup
        # handler matches
        #self.assertEqual(starter.startup_handler.stream, sys.stderr)
        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>
            debug-mode off
            <eventlog>
             level info
             <logfile>
               path <<INSTANCE_HOME>>/event.log
              level info
             </logfile>
           </eventlog>""")
        starter = self.get_starter(conf)
        starter.setupInitialLogging()
        # XXX need to check that log messages get written to
        # sys.stderr, not that the stream identity for the startup
        # handler matches
        #self.assertNotEqual(starter.startup_handler.stream, sys.stderr)

    def testSetupZServerThreads(self):
        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>
           zserver-threads 10""")
        starter = self.get_starter(conf)
        starter.setupZServer()
        from ZServer.PubCore import _n
        self.assertEqual(_n, 10)

    def testSetupServers(self):
        # We generate a random port number to test against, so that multiple
        # test runs of this at the same time can succeed
        port = random.randint(10000, 50000)
        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>
            <http-server>
                address %(http)s
            </http-server>
            <ftp-server>
               address %(ftp)s
            </ftp-server>""" % dict(http=port, ftp=port+1)
        )
        starter = self.get_starter(conf)
        # do the job the 'handler' would have done (call prepare)
        for server in conf.servers:
            server.prepare('', None, 'Zope2', {}, None)
        try:
            starter.setupServers()
            import ZServer
            self.assertEqual(conf.servers[0].__class__,
                             ZServer.HTTPServer.zhttp_server)
            self.assertEqual(conf.servers[1].__class__,
                             ZServer.FTPServer)
        finally:
            del conf.servers # should release servers
            pass

    def testDropPrivileges(self):
        # somewhat incomplete because we we're never running as root
        # when we test, but we test as much as we can
        if os.name != 'posix':
            return
        _old_getuid = os.getuid
        def _return0():
            return 0
        def make_starter(conf):
            # remove the debug handler, since we don't want junk on
            # stderr for the tests
            starter = self.get_starter(conf)
            starter.event_logger.removeHandler(starter.debug_handler)
            return starter
        try:
            os.getuid = _return0
            # no effective user
            conf = self.load_config_text("""
                instancehome <<INSTANCE_HOME>>""")
            starter = make_starter(conf)
            self.assertRaises(ZConfig.ConfigurationError,
                              starter.dropPrivileges)
            # cant find user in passwd database
            conf = self.load_config_text("""
                instancehome <<INSTANCE_HOME>>
                effective-user n0sucHuS3r""")
            starter = make_starter(conf)
            self.assertRaises(ZConfig.ConfigurationError,
                              starter.dropPrivileges)
            # can't specify '0' as effective user
            conf = self.load_config_text("""
                instancehome <<INSTANCE_HOME>>
                effective-user 0""")
            starter = make_starter(conf)
            self.assertRaises(ZConfig.ConfigurationError,
                              starter.dropPrivileges)
            # setuid to test runner's uid XXX will this work cross-platform?
            runnerid = _old_getuid()
            conf = self.load_config_text("""
                instancehome <<INSTANCE_HOME>>
                effective-user %s""" % runnerid)
            starter = make_starter(conf)
            finished = starter.dropPrivileges()
            self.assertTrue(finished)
        finally:
            os.getuid = _old_getuid

    def testSetupConfiguredLoggers(self):
        if sys.platform[:3].lower() == "win":
            return
        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>
            debug-mode off
            <eventlog>
             level info
             <logfile>
               path <<INSTANCE_HOME>>/event.log
              level info
             </logfile>
           </eventlog>
           <logger access>
             level info
             <logfile>
             path <<INSTANCE_HOME>>/Z2.log
             </logfile>
           </logger>
           <logger trace>
             level info
             <logfile>
             path <<INSTANCE_HOME>>/trace.log
             </logfile>
           </logger>
           """)
        try:
            starter = self.get_starter(conf)
            starter.setupInitialLogging()
            starter.info('hello')
            starter.setupFinalLogging()
            logger = logging.getLogger()
            self.assertEqual(logger.level, logging.INFO)
            l = open(os.path.join(TEMPNAME, 'event.log')).read()
            self.assertTrue(l.find('hello') > -1)
            self.assertTrue(os.path.exists(os.path.join(TEMPNAME, 'Z2.log')))
            self.assertTrue(os.path.exists(os.path.join(TEMPNAME,'trace.log')))
        finally:
            for name in ('event.log', 'Z2.log', 'trace.log'):
                try:
                    os.unlink(os.path.join(TEMPNAME, name))
                except:
                    pass
            self._clearHandlers()

    def testMakeLockFile(self):
        # put something in the way (it should be deleted)
        name = os.path.join(TEMPNAME, 'lock')
        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>
            lock-filename %s""" % name
                                     )
        f = open(name, 'ab')
        # On Windows, the first byte of the file is locked solid, and even
        # we (this process) can't read from it via a file object other
        # than the one passed to lock_file.  So we put a blank
        # in the test value first, so we can skip over it later.  Also,
        # because .seek(1) isn't well-defined for files opened in text
        # mode, we open the file in binary mode (above and below).
        f.write(' hello')
        f.close()
        try:
            starter = self.get_starter(conf)
            starter.makeLockFile()
            f = open(name, 'rb')
            f.seek(1)   # skip over the locked byte
            guts = f.read()
            f.close()
            self.assertFalse(guts.find('hello') > -1)
        finally:
            starter.unlinkLockFile()
            self.assertFalse(os.path.exists(name))

    def testMakePidFile(self):
        # put something in the way (it should be deleted)
        name = os.path.join(TEMPNAME, 'pid')
        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>
            pid-filename %s""" % name
                                     )
        f = open(name, 'a')
        f.write('hello')
        f.close()
        try:
            starter = self.get_starter(conf)
            starter.makePidFile()
            self.assertFalse(open(name).read().find('hello') > -1)
        finally:
            starter.unlinkPidFile()
            self.assertFalse(os.path.exists(name))

    def testConfigureInterpreter(self):
        import sys
        oldcheckinterval = sys.getcheckinterval()
        newcheckinterval = oldcheckinterval + 1
        conf = self.load_config_text("""
                    instancehome <<INSTANCE_HOME>>
                    python-check-interval %d
                    """ %  newcheckinterval  
        )
        try:
            starter = self.get_starter(conf)
            starter.setupInterpreter()
            self.assertEqual( sys.getcheckinterval() , newcheckinterval )
        finally:
            sys.setcheckinterval(oldcheckinterval)

    def testZopeRunConfigure(self):
        old_config = getConfiguration()
        try:
            os.mkdir(TEMPNAME)
            os.mkdir(TEMPPRODUCTS)
        except OSError, why:
            if why == errno.EEXIST:
                # already exists
                pass
        old_argv = sys.argv
        sys.argv = [sys.argv[0]]
        try:
            fname = os.path.join(TEMPNAME, 'zope.conf')
            from Zope2 import configure
            f = open(fname, 'w')
            f.write('instancehome %s\nzserver-threads 100\n' % TEMPNAME)
            f.flush()
            f.close()
            configure(fname)
            new_config = getConfiguration()
            self.assertEqual(new_config.zserver_threads, 100)
        finally:
            sys.argv = old_argv
            try:
                os.unlink(fname)
            except:
                pass
            setConfiguration(old_config)


def test_suite():
    return unittest.makeSuite(ZopeStarterTestCase)
