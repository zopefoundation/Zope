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

import os
import sys
import socket
import re

import ZConfig

def start_zope(cfg):
    # set up our initial logging environment (log everything to stderr
    # if we're not in debug mode).
    import zLOG
    import logging

    # don't initialize the event logger from the environment
    zLOG._call_initialize = 0

    from zLOG.LogHandlers import StartupHandler

    # we log events to the root logger, which is backed by a
    # "StartupHandler" log handler.  The "StartupHandler" outputs to
    # stderr but also buffers log messages.  When the "real" loggers
    # are set up, we flush accumulated messages in StartupHandler's
    # buffers to the real logger.
    startup_handler = StartupHandler(sys.stderr)
    formatter = zLOG.EventLogger.formatters['file']
    startup_handler.setFormatter(formatter)
    if not cfg.debug_mode:
        # prevent startup messages from going to stderr if we're not
        # in debug mode
        if os.path.exists('/dev/null'): # unix
            devnull = '/dev/null'
        else: # win32
            devnull = 'nul:'
        startup_handler = StartupHandler(open(devnull, 'w'))

    # set up our event logger temporarily with a startup handler
    event_logger = zLOG.EventLogger.EventLogger.logger
    event_logger.addHandler(startup_handler)
    # set the initial logging level to INFO (this will be changed by the
    # zconfig settings later)
    event_logger.level = logging.INFO

    # set a locale if one has been specified in the config
    if cfg.locale:
        do_locale(cfg.locale)

    # Increase the number of threads
    import ZServer
    ZServer.setNumberOfThreads(cfg.zserver_threads)

    # Start ZServer servers before we setuid so we can bind to low ports:
    socket_err = (
        'There was a problem starting a server of type "%s". '
        'This may mean that your user does not have permission to '
        'bind to the port which the server is trying to use or the '
        'port may already be in use by another application. '
        '(%s)'
        )
    servers = []
    for server in cfg.servers:
        # create the server from the server factory
        # set up in the config
        try:
            servers.append(server.create())
        except socket.error,e:
            raise ZConfig.ConfigurationError(socket_err
                                             % (server.servertype(),e[1]))
    cfg.servers = servers

    # do stuff that only applies to posix platforms (setuid mainly)
    if os.name == 'posix':
        do_posix_stuff(cfg)

    # Import Zope
    import Zope
    Zope.startup()

    # this is a bit of a white lie, since we haven't actually successfully
    # started yet, but we're pretty close and we want this output to
    # go to the startup logger in order to prevent the kinds of email messages 
    # to the Zope maillist in which people claim that Zope has "frozen"
    # after it has emitted ZServer messages ;-)
    zLOG.LOG('Zope', zLOG.INFO, 'Ready to handle requests')

    if not cfg.zserver_read_only_mode:
        # lock_file is used for the benefit of zctl-like systems, so they
        # can tell whether Zope is already running before attempting to fire
        # it off again.
        #
        # We aren't concerned about locking the file to protect against
        # other Zope instances running from our CLIENT_HOME, we just
        # try to lock the file to signal that zctl should not try to
        # start Zope if *it* can't lock the file; we don't panic
        # if we can't lock it.
        # we need a separate lock file because on win32, locks are not
        # advisory, otherwise we would just use the pid file
        from Zope.Startup.misc.lock_file import lock_file
        lock_filename = cfg.lock_filename
        try:
            if os.path.exists(lock_filename):
                os.unlink(lock_filename)
            LOCK_FILE = open(lock_filename, 'w')
            lock_file(LOCK_FILE)
            LOCK_FILE.write(str(os.getpid()))
            LOCK_FILE.flush()
        except IOError:
            pass

        # write the pid into the pidfile if possible
        pid_filename = cfg.pid_filename
        try:
            if os.path.exists(pid_filename):
                os.unlink(pid_filename)
            f = open(pid_filename, 'w')
            f.write(str(os.getpid()))
            f.close()
        except IOError:
            pass
        
        # Now that we've successfully setuid'd, we can log to
        # somewhere other than stderr.  Activate the configured logs:
        if cfg.access is not None:
            cfg.access()
        if cfg.trace is not None:
            cfg.trace()

        # flush buffered startup messages to event logger
        event_logger.removeHandler(startup_handler)
        if cfg.eventlog is not None:
            logger = cfg.eventlog()
            startup_handler.flushBufferTo(logger)

    # Start Medusa, Ye Hass!
    try:
        import Lifetime
        Lifetime.loop()
        sys.exit(ZServer.exit_code)
    finally:
        if not cfg.zserver_read_only_mode:
            try:
                os.unlink(pid_filename)
            except OSError:
                pass
            try:
                LOCK_FILE.close()
                os.unlink(lock_filename)
            except OSError:
                pass

def _warn_nobody():
    import zLOG
    zLOG.LOG("Zope", zLOG.INFO, ("Running Zope as 'nobody' can compromise "
                                 "your Zope files; consider using a "
                                 "dedicated user account for Zope"))

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

def do_posix_stuff(cfg):
    import zLOG
    import zdaemon
    import pwd
    from Signals import Signals
    Signals.registerZopeSignals()

    # Warn if we were started as nobody.
    if os.getuid():
        if pwd.getpwuid(os.getuid())[0] == 'nobody':
            _warn_nobody()

    # Drop root privileges if we have them, and do some sanity checking
    # to make sure we're not starting with an obviously insecure setup.
    if os.getuid() == 0:
        UID  = cfg.effective_user
        if UID == None:
            msg = ('A user was not specified to setuid to; fix this to '
                   'start as root (change the effective_user directive '
                   'in zope.conf)')
            zLOG.LOG('Zope', zLOG.PANIC, msg)
            raise ZConfig.ConfigurationError(msg)
        # stuff about client home faults removed (real effective user
        # support now)
        try:
            UID = int(UID)
        except (TypeError, ValueError):
            pass
        gid = None
        if isinstance(UID, str):
            uid = pwd.getpwnam(UID)[2]
            gid = pwd.getpwnam(UID)[3]
        elif isinstance(UID, int):
            uid = pwd.getpwuid(UID)[2]
            gid = pwd.getpwuid(UID)[3]
            UID = pwd.getpwuid(UID)[0]
        else:
            zLOG.LOG("Zope", zLOG.ERROR, ("Can't find UID %s" % UID))
            raise ZConfig.ConfigurationError('Cant find UID %s' % UID)
        if UID == 'nobody':
            _warn_nobody()
        if gid is not None:
            try:
                import initgroups
                initgroups.initgroups(UID, gid)
                os.setgid(gid)
            except OSError:
                zLOG.LOG("Zope", zLOG.INFO,
                         'Could not set group id of effective user',
                         error=sys.exc_info())
        os.setuid(uid)
        zLOG.LOG("Zope", zLOG.INFO,
                 'Set effective user to "%s"' % UID)

    if not cfg.debug_mode:
        # umask is silly, blame POSIX.  We have to set it to get its value.
        current_umask = os.umask(0)
        os.umask(current_umask)
        if current_umask != 077:
            current_umask = '%03o' % current_umask
            zLOG.LOG("Zope", zLOG.INFO, (
                'Your umask of %s may be too permissive; for the security of '
                'your Zope data, it is recommended you use 077' % current_umask
                ))


def do_locale(locale_id):
    # workaround to allow unicode encoding conversions in DTML
    import codecs
    dummy = codecs.lookup('iso-8859-1')

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
                'The specified locale "%s" is not supported by your system.\n'
                'See your operating system documentation for more\n'
                'information on locale support.' % locale_id
                )


