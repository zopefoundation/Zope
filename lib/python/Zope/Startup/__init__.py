""" Startup package.  Responsible for startup configuration of Zope """

import os
import sys
import socket
import re

import ZConfig

from misc.lock_file import lock_file
from cmdline import getOptions, getOptionDescriptions # exported

# global to hold config structures
_schema = None
_configuration = None

def getConfiguration():
    return _configuration

def getSchema():
    global _schema
    if _schema is None:
        here = os.path.dirname(__file__)
        path = os.path.join(here, 'zopeschema.xml')
        _schema = ZConfig.loadSchema(path)
    return _schema

def getSchemaKeys():
    schema = getSchema()
    return schema.getchildnames()

def configure(config_location, options):
    global _configuration
    import handlers
    schema = getSchema()
    _configuration, handler = ZConfig.loadConfig(schema, config_location)
    handlers.handleConfig(_configuration, handler, options)
    return _configuration

def start_zope(config_location, options):
    check_python_version()
    cfg = configure(config_location, options)

    if cfg.zope_home not in sys.path:
        sys.path.insert(0, cfg.zope_home)

    if cfg.software_home not in sys.path:
        sys.path.insert(0, cfg.software_home)

    sys.path = filter(None, sys.path) # strip empties out of sys.path

    # set up our initial logging environment (log everything to stderr
    # if we're not in debug mode).
    import zLOG

    # don't initialize the event logger from the environment
    zLOG._call_initialize = 0
    import logging

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
    event_logger = logging.getLogger('event')
    event_logger.addHandler(startup_handler)

    # set a locale if one has been specified in the config
    cfg.locale and do_locale(cfg.locale)

    # goofy source_port clients business
    dav_clients = cfg.webdav_source_user_agents
    if dav_clients:
        sys.WEBDAV_SOURCE_PORT_CLIENTS = re.compile(dav_clients).search

    # make sure to import zdaemon before zserver or weird things
    # begin to happen
    import zdaemon

    # Import ZServer before we open the database or get at interesting
    # application code so that ZServer's asyncore gets to be the
    # official one. Also gets SOFTWARE_HOME, INSTANCE_HOME, and CLIENT_HOME
    import ZServer

    # Increase the number of threads
    from ZServer import setNumberOfThreads
    setNumberOfThreads(cfg.zserver_threads)

    # if we're not using ZDaemon or if we're the child of a Zdaemon process,
    # start ZServer servers before we setuid so we can bind to low ports
    if not cfg.use_daemon_process or (
        cfg.use_daemon_process and os.environ.get('ZDAEMON_MANAGED')
        ):
        socket_err = (
            'There was a problem starting a server of type "%s". '
            'This may mean that your user does not have permission to '
            'bind to the port which the server is trying to use or the '
            'port may already be in use by another application.'
            )
        for server_type, server in cfg.servers:
            # create the server from the server factory
            # set up in the config
            try:
                server()
            except socket.error:
                raise ZConfig.ConfigurationError(socket_err % server_type)

    # do stuff that only applies to posix platforms (setuid, daemonizing)
    if os.name == 'posix':
        do_posix_stuff(cfg)

    # Import Zope
    import Zope
    Zope.startup()

    if not cfg.zserver_read_only_mode:
        # lock_file is used for the benefit of zctl, so it can tell whether
        # Zope is already running before attempting to fire it off again.
        # We aren't concerned about locking the file to protect against
        # other Zope instances running from our CLIENT_HOME, we just
        # try to lock the file to signal that zctl should not try to
        # start Zope if *it* can't lock the file; we don't panic
        # if we can't lock it.
        # we need a separate lock file because on win32, locks are not
        # advisory, otherwise we would just use the pid file
        lock_filename = (cfg.lock_filename or
                         os.path.join(cfg.instance_home, 'var', 'Z2.lock'))

        try:
            if os.path.exists(lock_filename):
                os.unlink(lock_filename)
            LOCK_FILE = open(lock_filename, 'w')
            lock_file(LOCK_FILE)
        except IOError:
            pass

        # write pid file if zdaemon didn't do it already
        if not cfg.use_daemon_process:
            pf = open(cfg.pid_filename, 'w')
            pid='%s\n' % os.getpid()
            pf.write(pid)
            pf.close()

        # now that we've successfully setuid'd, we can log to
        # somewhere other than stderr.  We rely on config
        # to set up our logging properly.
        for logger_name in ('access', 'trace'):
            factory = getattr(cfg, logger_name)
            if factory:
                logger = factory() # activate the logger

        # flush buffered startup messages to event logger
        if cfg.eventlog:
            logger = cfg.eventlog()
            startup_handler.flushBufferTo(logger)

        event_logger.removeHandler(startup_handler)

    zLOG.LOG('Zope', zLOG.INFO, 'Ready to handle requests')

    # Start Medusa, Ye Hass!
    sys.ZServerExitCode=0
    try:
        import Lifetime
        Lifetime.loop()
        sys.exit(sys.ZServerExitCode)
    finally:
        if not cfg.zserver_read_only_mode:
            try:
                os.unlink(cfg.pid_filename)
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
    optimum_version = '2.2.2'
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

    # try to use a management daemon process.  We do this after we setuid so
    # we don't write our pidfile out as root.
    if cfg.use_daemon_process and not cfg.zserver_read_only_mode:
        import App.FindHomes
        sys.ZMANAGED=1
        # zdaemon.run creates a process which "manages" the actual Zope
        # process (restarts it if it dies).  The management process passes
        # along signals that it receives to its child.
        zdaemon.run(sys.argv, cfg.pid_filename)

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


