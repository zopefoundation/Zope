##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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

""" Startup package.  Responsible for startup configuration of Zope """

import logging
import os
import re
import sys
import socket

import ZConfig

logger = logging.getLogger("Zope")
started = False

def start_zope(cfg):
    """The function called by run.py which starts a Zope appserver."""
    global started
    if started:
        # dont allow any code to call start_zope twice.
        return

    check_python_version()
    if sys.platform[:3].lower() == "win":
        starter = WindowsZopeStarter(cfg)
    else:
        starter = UnixZopeStarter(cfg)
    starter.setupLocale()
    # we log events to the root logger, which is backed by a
    # "StartupHandler" log handler.  The "StartupHandler" outputs to
    # stderr but also buffers log messages.  When the "real" loggers
    # are set up, we flush accumulated messages in StartupHandler's
    # buffers to the real logger.
    starter.setupInitialLogging()
    starter.setupSecurityOptions()
    # Start ZServer servers before we drop privileges so we can bind to
    # "low" ports:
    starter.setupZServerThreads()
    starter.setupServers()
    # drop privileges after setting up servers
    starter.dropPrivileges()
    starter.makeLockFile()
    starter.makePidFile()
    starter.startZope()
    starter.registerSignals()
    # emit a "ready" message in order to prevent the kinds of emails
    # to the Zope maillist in which people claim that Zope has "frozen"
    # after it has emitted ZServer messages.
    logger.info('Ready to handle requests')
    starter.setupFinalLogging()

    started = True

    # the mainloop.
    try:
        import ZServer
        import Lifetime
        Lifetime.loop()
        sys.exit(ZServer.exit_code)
    finally:
        starter.unlinkLockFile()
        starter.unlinkPidFile()
        started = False

class ZopeStarter:
    """This is a class which starts a Zope server.

    Making it a class makes it easier to test.
    """
    def __init__(self, cfg):
        self.cfg = cfg
        self.event_logger = logging.getLogger()

    # XXX does anyone actually use these three?

    def info(self, msg):
        logger.info(msg)

    def panic(self, msg):
        logger.critical(msg)

    def error(self, msg):
        logger.error(msg)

    def setupSecurityOptions(self):
        import AccessControl
        AccessControl.setImplementation(
            self.cfg.security_policy_implementation)
        AccessControl.setDefaultBehaviors(
            not self.cfg.skip_ownership_checking,
            not self.cfg.skip_authentication_checking)

    def setupLocale(self):
        # set a locale if one has been specified in the config
        if not self.cfg.locale:
            return

        # workaround to allow unicode encoding conversions in DTML
        import codecs
        dummy = codecs.lookup('iso-8859-1')

        locale_id = self.cfg.locale

        if locale_id is not None:
            try:
                import locale
            except:
                raise ZConfig.ConfigurationError(
                    'The locale module could not be imported.\n'
                    'To use localization options, you must ensure\n'
                    'that the locale module is compiled into your\n'
                    'Python installation.'
                    )
            try:
                locale.setlocale(locale.LC_ALL, locale_id)
            except:
                raise ZConfig.ConfigurationError(
                    'The specified locale "%s" is not supported by your'
                    'system.\nSee your operating system documentation for '
                    'more\ninformation on locale support.' % locale_id
                    )

    def setupZServerThreads(self):
        # Increase the number of threads
        import ZServer
        ZServer.setNumberOfThreads(self.cfg.zserver_threads)

    def setupServers(self):
        socket_err = (
            'There was a problem starting a server of type "%s". '
            'This may mean that your user does not have permission to '
            'bind to the port which the server is trying to use or the '
            'port may already be in use by another application. '
            '(%s)'
            )
        servers = []
        for server in self.cfg.servers:
            # create the server from the server factory
            # set up in the config
            try:
                servers.append(server.create())
            except socket.error,e:
                raise ZConfig.ConfigurationError(socket_err
                                                 % (server.servertype(),e[1]))
        self.cfg.servers = servers

    def dropPrivileges(self):
        return dropPrivileges(self.cfg)

    def setupConfiguredLoggers(self):
        if self.cfg.zserver_read_only_mode:
            # no log files written in read only mode
            return

        if self.cfg.eventlog is not None:
            self.cfg.eventlog()
        if self.cfg.access is not None:
            self.cfg.access()
        if self.cfg.trace is not None:
            self.cfg.trace()

    def startZope(self):
        # Import Zope
        import Zope
        Zope.startup()

    def makeLockFile(self):
        if not self.cfg.zserver_read_only_mode:
            # lock_file is used for the benefit of zctl-like systems, so they
            # can tell whether Zope is already running before attempting to
            # fire it off again.
            #
            # We aren't concerned about locking the file to protect against
            # other Zope instances running from our CLIENT_HOME, we just
            # try to lock the file to signal that zctl should not try to
            # start Zope if *it* can't lock the file; we don't panic
            # if we can't lock it.
            # we need a separate lock file because on win32, locks are not
            # advisory, otherwise we would just use the pid file
            from Zope.Startup.misc.lock_file import lock_file
            lock_filename = self.cfg.lock_filename
            try:
                if os.path.exists(lock_filename):
                    os.unlink(lock_filename)
                self.lockfile = open(lock_filename, 'w')
                lock_file(self.lockfile)
                self.lockfile.write(str(os.getpid()))
                self.lockfile.flush()
            except IOError:
                pass

    def makePidFile(self):
        if not self.cfg.zserver_read_only_mode:
            # write the pid into the pidfile if possible
            try:
                if os.path.exists(self.cfg.pid_filename):
                    os.unlink(self.cfg.pid_filename)
                f = open(self.cfg.pid_filename, 'w')
                f.write(str(os.getpid()))
                f.close()
            except IOError:
                pass

    def unlinkPidFile(self):
        if not self.cfg.zserver_read_only_mode:
            try:
                os.unlink(self.cfg.pid_filename)
            except OSError:
                pass

    def unlinkLockFile(self):
        if not self.cfg.zserver_read_only_mode:
            try:
                self.lockfile.close()
                os.unlink(self.cfg.lock_filename)
            except OSError:
                pass


class WindowsZopeStarter(ZopeStarter):

    def registerSignals(self):
        pass

    def setupInitialLogging(self):
        self.setupConfiguredLoggers()

    def setupFinalLogging(self):
        pass


class UnixZopeStarter(ZopeStarter):

    def registerSignals(self):
        from Signals import Signals
        Signals.registerZopeSignals([self.cfg.eventlog,
                                     self.cfg.access,
                                     self.cfg.trace])

    def setupInitialLogging(self):
        # set up our initial logging environment (log everything to stderr
        # if we're not in debug mode).
        from ZConfig.components.logger.loghandler import StartupHandler

        if self.cfg.eventlog is not None:
            # get the lowest handler level.  This is the effective level
            # level at which which we will spew messages to the console
            # during startup.
            level = self.cfg.eventlog.getLowestHandlerLevel()
        else:
            level = logging.INFO

        self.startup_handler = StartupHandler(sys.stderr)
        self.startup_handler.setLevel(level)
        formatter = logging.Formatter(
            fmt='------\n%(asctime)s %(levelname)s %(name)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S')
        if not self.cfg.debug_mode:
            # prevent startup messages from going to stderr if we're not
            # in debug mode
            self.startup_handler = StartupHandler(open('/dev/null', 'w'))
        self.startup_handler.setFormatter(formatter)

        # set up our event logger temporarily with a startup handler only
        self.event_logger.handlers = []
        self.event_logger.addHandler(self.startup_handler)
        # set the initial logging level (this will be changed by the
        # zconfig settings later)
        self.event_logger.level = level

    def setupFinalLogging(self):
        if self.startup_handler in self.event_logger.handlers:
            self.event_logger.removeHandler(self.startup_handler)
        self.setupConfiguredLoggers()
        # flush buffered startup messages to event logger
        logger = logging.getLogger('event')
        self.startup_handler.flushBufferTo(logger)


def check_python_version():
    # check for Python version
    python_version = sys.version.split()[0]
    optimum_version = '2.2.3'
    if python_version < '2.2':
        raise ZConfig.ConfigurationError(
            'Invalid python version ' + python_version)
    if python_version[:3] == '2.2':
        if python_version[4:5] < '2':
            err = ('You are running Python version %s.  This Python version '
                   'has known bugs that may cause Zope to run improperly. '
                   'Consider upgrading to Python %s\n' %
                   (python_version, optimum_version))
            sys.stderr.write(err)

def dropPrivileges(cfg):
    # Drop root privileges if we have them and we're on a posix platform.
    # This needs to be a function so it may be used outside of Zope
    # appserver startup (e.g. from zopectl debug)
    if os.name != 'posix':
        return

    if os.getuid() != 0:
        return

    import pwd

    effective_user  = cfg.effective_user
    if effective_user is None:
        msg = ('A user was not specified to setuid to; fix this to '
               'start as root (change the effective-user directive '
               'in zope.conf)')
        logger.critical(msg)
        raise ZConfig.ConfigurationError(msg)

    try:
        uid = int(effective_user)
    except ValueError:
        try:
            pwrec = pwd.getpwnam(effective_user)
        except KeyError:
            msg = "Can't find username %r" % effective_user
            logger.error(msg)
            raise ZConfig.ConfigurationError(msg)
        uid = pwrec[2]
    else:
        try:
            pwrec = pwd.getpwuid(uid)
        except KeyError:
            msg = "Can't find uid %r" % uid
            logger.error(msg)
            raise ZConfig.ConfigurationError(msg)
    gid = pwrec[3]

    if uid == 0:
        msg = 'Cannot start Zope with the effective user as the root user'
        logger.error(msg)
        raise ZConfig.ConfigurationError(msg)

    try:
        import initgroups
        initgroups.initgroups(effective_user, gid)
        os.setgid(gid)
    except OSError:
        logger.exception('Could not set group id of effective user')

    os.setuid(uid)
    logger.info('Set effective user to "%s"' % effective_user)
    return 1 # for unit testing purposes 
