##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Tests of the ZopeStarter class """

import os
import cStringIO
import tempfile
import unittest

import ZConfig
import Zope.Startup
from Zope.Startup import ZopeStarter

from App.config import getConfiguration
import logging

TEMPNAME = tempfile.mktemp()
TEMPPRODUCTS = os.path.join(TEMPNAME, "Products")

def getSchema():
    startup = os.path.dirname(os.path.realpath(Zope.Startup.__file__))
    schemafile = os.path.join(startup, 'zopeschema.xml')
    return ZConfig.loadSchema(schemafile)

# try to preserve logging state so we don't screw up other unit tests
# that come later

logger_states = {}
for name in ('event', 'trace', 'access'):
    logger = logging.getLogger(name)
    logger_states[name] = {'level':logger.level,
                           'propagate':logger.propagate,
                           'handlers':logger.handlers,
                           'filters':logger.filters}

class ZopeStarterTestCase(unittest.TestCase):

    def setUp(self):
        self.schema = getSchema()
        self.original_event_logger = logging.getLogger

    def tearDown(self):
        try:
            os.rmdir(TEMPPRODUCTS)
            os.rmdir(TEMPNAME)
        except:
            pass
        # reset logger states
        for name in ('event', 'access', 'trace'):
            logger = logging.getLogger(name)
            logger.__dict__.update(logger_states[name])

    def load_config_text(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        schema = self.schema
        text = "instancehome <<INSTANCE_HOME>>\n" + text
        sio = cStringIO.StringIO(
            text.replace("<<INSTANCE_HOME>>", TEMPNAME))
        try:
            os.mkdir(TEMPNAME)
            os.mkdir(TEMPPRODUCTS)
        except OSError, why:
            if why == 17:
                # already exists
                pass
        conf, handler = ZConfig.loadConfigFile(schema, sio)
        self.assertEqual(conf.instancehome, TEMPNAME)
        return conf

    def testSetupLocale(self):
        # XXX this almost certainly won't work on all systems
        import locale
        try:
            conf = self.load_config_text("locale fr_FR")
            starter = ZopeStarter(conf)
            starter.setupLocale()
            self.assertEqual(locale.getlocale(), ['fr_FR', 'ISO8859-1'])
        finally:
            # resest to system-defined locale
            locale.setlocale(locale.LC_ALL, '')

    def testSetupStartupHandler(self):
        import zLOG
        import sys
        conf = self.load_config_text("""
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
        starter = ZopeStarter(conf)
        starter.setupStartupHandler()
        self.assert_(not zLOG._call_initialize)
        self.assertEqual(starter.startup_handler.formatter,
                         zLOG.EventLogger.formatters['file'])

        # startup handler should take on the level of the event log handler
        # with the lowest level
        self.assertEqual(starter.startup_handler.level, 15) # 15 is BLATHER
        self.assertEqual(starter.startup_handler,
                     zLOG.EventLogger.EventLogger.logger.handlers[0])
        self.assertEqual(zLOG.EventLogger.EventLogger.logger.level,
                         15)
        self.assertEqual(len(zLOG.EventLogger.EventLogger.logger.handlers), 1)
        self.failUnlessEqual(starter.startup_handler.stream, sys.stderr)
        conf = self.load_config_text("""
            debug-mode off
            <eventlog>
             level info
             <logfile>
               path <<INSTANCE_HOME>>/event.log
              level info
             </logfile>
           </eventlog>""")
        starter = ZopeStarter(conf)
        starter.setupStartupHandler()
        self.failIfEqual(starter.startup_handler.stream, sys.stderr)

    def testSetupZServerThreads(self):
        conf = self.load_config_text("zserver-threads 10")
        starter = ZopeStarter(conf)
        starter.setupZServerThreads()
        from ZServer.PubCore import _n
        self.assertEqual(_n, 10)

    def testSetupServers(self):
        conf = self.load_config_text("""
            <http-server>
                address 18092
            </http-server>
            <ftp-server>
               address 18093
            </ftp-server>""")
        starter = ZopeStarter(conf)
        # do the job the 'handler' would have done (call prepare)
        for server in conf.servers:
            server.prepare('', None, 'Zope', {}, None)
        try:
            starter.setupServers()
            import ZServer
            self.assertEqual(conf.servers[0].__class__,
                             ZServer.HTTPServer.zhttp_server)
            self.assertEqual(conf.servers[1].__class__,
                             ZServer.FTPServer)
        finally:
            del conf.servers # should release servers

    def testSetupServersWithConflict(self):
        conf = self.load_config_text("""
            <http-server>
                address 18092
            </http-server>
            <ftp-server>
               address 18092 # conflict
            </ftp-server>""")
        starter = ZopeStarter(conf)
        # do the job the 'handler' would have done (call prepare)
        for server in conf.servers:
            server.prepare('', None, 'Zope', {}, None)
        try:
            self.assertRaises(ZConfig.ConfigurationError, starter.setupServers)
        finally:
            del conf.servers

    def testDropPrivileges(self):
        # somewhat incomplete because we we're never running as root
        # when we test, but we test as much as we can
        if os.name != 'posix':
            return
        _old_getuid = os.getuid
        def _return0():
            return 0
        try:
            os.getuid = _return0
            # no effective user
            conf = self.load_config_text("")
            starter = ZopeStarter(conf)
            self.assertRaises(ZConfig.ConfigurationError,
                              starter.dropPrivileges)
            # cant find user in passwd database
            conf = self.load_config_text("effective-user n0sucHuS3r")
            starter = ZopeStarter(conf)
            self.assertRaises(ZConfig.ConfigurationError,
                              starter.dropPrivileges)
            # can't specify '0' as effective user
            conf = self.load_config_text("effective-user 0")
            starter = ZopeStarter(conf)
            self.assertRaises(ZConfig.ConfigurationError,
                              starter.dropPrivileges)
            # setuid to test runner's uid XXX will this work cross-platform?
            runnerid = _old_getuid()
            conf = self.load_config_text("effective-user %s" % runnerid)
            starter = ZopeStarter(conf)
            finished = starter.dropPrivileges()
            self.failUnless(finished)
        finally:
            os.getuid = _old_getuid

    def testSetupConfiguredLoggers(self):
        import zLOG
        import logging
        import sys
        conf = self.load_config_text("""
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
            starter = ZopeStarter(conf)
            starter.setupStartupHandler()
            starter.info('hello')
            starter.removeStartupHandler()
            starter.setupConfiguredLoggers()
            self.assertEqual(zLOG.EventLogger.EventLogger.logger.level,
                             logging.INFO)
            starter.flushStartupHandlerBuffer()
            l = open(os.path.join(TEMPNAME, 'event.log')).read()
            self.failUnless(l.find('hello') > -1)
            self.failUnless(os.path.exists(os.path.join(TEMPNAME, 'Z2.log')))
            self.failUnless(os.path.exists(os.path.join(TEMPNAME,'trace.log')))
        finally:
            for name in ('event.log', 'Z2.log', 'trace.log'):
                try:
                    os.unlink(os.path.join(TEMPNAME, name))
                except:
                    pass

    def testMakeLockFile(self):
        # put something in the way (it should be deleted)
        name = os.path.join(TEMPNAME, 'lock')
        conf = self.load_config_text("lock-filename %s" % name)
        f = open(name, 'a')
        f.write('hello')
        f.close()
        try:
            starter = ZopeStarter(conf)
            starter.makeLockFile()
            self.failIf(open(name).read().find('hello') > -1)
        finally:
            starter.unlinkLockFile()
            self.failIf(os.path.exists(name))

    def testMakePidFile(self):
        # put something in the way (it should be deleted)
        name = os.path.join(TEMPNAME, 'pid')
        conf = self.load_config_text("pid-filename %s" % name)
        f = open(name, 'a')
        f.write('hello')
        f.close()
        try:
            starter = ZopeStarter(conf)
            starter.makePidFile()
            self.failIf(open(name).read().find('hello') > -1)
        finally:
            starter.unlinkPidFile()
            self.failIf(os.path.exists(name))

def test_suite():
    return unittest.makeSuite(ZopeStarterTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
