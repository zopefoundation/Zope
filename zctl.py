#!/usr/bin/env python
# -*- python -*-

"""Control Zope, and ZEO server if it's configured

Usage:

    zctl.py start [confname ...] [--zeo -arg ... [--zope]] -arg ...

    zctl.py stop [confname ...]

    zctl.py stop_all

    zctl.py start_zeo

    zctl.py stop_zeo

    zctl.py status [confname ...]

    zctl.py make_cgi [filename]

    zctl.py debug

    zctl.py test filename

    zctl.py do [-i] [-f filename]* commands

    zctl.py script filename

The file 'zconfig.py' must exist in the INSTANCE_HOME where 'zctl.py' lives.
It sets up configuration information for Zope, and optionally for ZEO.
Additional Zope configurations may be defined by creating subdirectories
of the INSTANCE_HOME containing 'zconfig.py'.  If you specify the name of
one or more of these subdirectories in a 'zctl.py start' or 'zctl.py stop',
that configuration will be started or stopped instead of the default.

'zctl.py make_cgi' will write PCGI settings to the file you specify, or to
'Zope.cgi' if the name is omitted.

'zctl.py debug' will launch an interactive Python session with the Zope
application object loaded as 'app'.

'zctl.py script filename' or 'zctl.py test filename' will run the
Python file in the same type of context as provided by 'zctl.py
debug'.

'zctl.py do' will run specified Python commands.  It may optionally run
Python files and start an interactive session.


"""

import sys, os, socket, time, string
from os.path import isfile, isdir, abspath
pjoin = os.path.join
psplit = os.path.split
env = os.environ
run = os.system

# Find out where we are, and where Python is.
if not sys.argv[0]: HERE = '.'
else: HERE = psplit(sys.argv[0])[0]
HERE = CLIENT_HOME = abspath(HERE)
PYTHON = '"%s"' % sys.executable
ZOPE_ENV = {}
ZEO = {} # ZEO is off by default
ZEO_ENV = {}

# Load configuration data into global variables
ZOPE_CONFIG = pjoin(HERE, 'zconfig.py')
if not isfile(ZOPE_CONFIG):
    print 'Zope configuration file "zconfig.py" not found.'
    sys.exit(1)
execfile(ZOPE_CONFIG, globals())

# Poke environment variables needed by Zope and ZEO
env['INSTANCE_HOME'] = HERE
env['PYTHONHOME'] = ZOPE_HOME = abspath(ZOPE_HOME)
for k, v in ZEO.items():
    env[k] = str(v)

# Commands

def zctl_start(args):
    """Start Zope when ZEO is reachable, starting ZEO first if necessary."""
    clients = []
    zeo_args = []
    zope_args = []
    while args and args[0][:1] != '-':
        clients.append(args.pop(0))
    while args:
        if args[0] == '--zeo':
            args.pop(0)
            while args and args[0][:2] != '--':
                zeo_args.append(args.pop(0))
        else:
            if args[0] == '--zope':
                args.pop(0)
            while args and args[0][:2] != '--':
                zope_args.append(args.pop(0))
    if not clients:
        clients.append('default')

    cmd = '%s "%s/z2.py" %%s' % (PYTHON, ZOPE_HOME)
    global ZOPE_PORT, ZOPE_LOG, ZOPE_OPTS, ZOPE_ENV, ZEO_ENV
    for client in clients:
        args = list(zope_args)
        if client != 'default':
            ZOPE_PORT = ZOPE_LOG = ZOPE_OPTS = ''
            global CLIENT_HOME
            CLIENT_HOME = pjoin(HERE, client)
            conf = pjoin(CLIENT_HOME, 'zconfig.py')
            if not (isdir(CLIENT_HOME) and isfile(conf)):
                print 'Client configuration file "%s" was not found.' % conf
                continue
            execfile(conf, globals())
            args.append('"CLIENT_HOME=%s"' % CLIENT_HOME)
        if ZOPE_OPTS:
            args.insert(0, ZOPE_OPTS)
        if ZOPE_PORT:
            args.insert(0, '-P %s' % ZOPE_PORT)
        if ZOPE_LOG:
            args.append('"STUPID_LOG_FILE=%s"' % ZOPE_LOG)
        for k,v in ZOPE_ENV.items():
            env[k] = str(v)
        if ZEO:
            zctl_start_zeo(zeo_args)
        print 'Starting %s Zope...' % client
        run(cmd % string.join(args))
        
def zctl_start_zeo(args):
    """Try to start ZEO."""
    for item in ZEO_ENV.items():
        args.append("%s=%s" % item)
    host = ZEO.get('ZEO_SERVER_NAME', 'localhost')
    port = ZEO['ZEO_SERVER_PORT']
    if host == 'localhost' and not _check_for_service(host, port):
        print "Starting ZEO server on", port
        cmd = '%s %s/lib/python/ZEO/start.py -p %s %s &' % (
            PYTHON, ZOPE_HOME, port, string.join(args)
            )
        run(cmd)
    count = 0
    while not _check_for_service(host, port):
        count = count + 1
        if count > ZEO_WAIT_BAILOUT:
            print ("ZEO connect failure, on port %s after %d seconds"
                   % (port, ZEO_WAIT_BAILOUT))
            sys.exit(1)
        print "waiting for ZEO server to start %d/%d" % (count,
                                                         ZEO_WAIT_BAILOUT)
        time.sleep(1)
    #print "ZEO server ready."

def zctl_stop_zeo(args):
    """Stop the ZEO server."""
    try:
        pids = open('%s/var/ZEO_SERVER.pid' % HERE, 'r').read()
    except:
        return
    print "Stopping ZEO pid: %s" % pids
    run('kill %s' % pids)

def zctl_stop(args):
    """Stop client(s)."""
    if not args:
        args = ['var']
    for client in args:
        pidf = pjoin(HERE, client, 'Z2.pid')
        if not isfile(pidf):
            print '"%s" was not found' % pidf
            continue
        pids=open(pidf).read()
        print 'Stopping Zope process %s' % pids
        run('kill %s' % open(pidf, 'r').read())
    return

def zctl_stop_all(args):
    "Stop clients and ZEO server"
    zctl_stop(args)
    zctl_stop_zeo(args)
    return

def zctl_status(args):
    """Print status."""
    print "NAME\tPORT\tPIDS"
    if ZEO:
        host = ZEO.get('ZEO_SERVER_NAME', 'localhost')
        port = ZEO['ZEO_SERVER_PORT']
        pids = ''
        if _check_for_service(host, port):
            if host == 'localhost':
                pids = open('%s/var/ZEO_SERVER.pid' % HERE, 'r').read()
            else:
                pids = 'unknown'
        print "ZEO\t%s\t%s" % (port, pids)
    if not args:
        import glob
        for client in glob.glob('%s/*/conf.py' % HERE):
            args.append(psplit(psplit(client)[0])[1])
    for client in args:
        pidf = pjoin(HERE, client, 'Z2.pid')
        if isfile(pidf):
            pids = open(pidf, 'r').read()
        else:
            pids = 'not found'
        print '%s\t%s\t%s' % (client, '', pids)

def zctl_make_cgi(args):
    """Create a PCGI parameter file."""
    if args:
        fname = args.pop(0)
    else:
        fname = 'Zope.cgi'
    write = open(fname, 'w').write
    write('''\
#!%(ZOPE_HOME)s/pcgi/pcgi-wrapper
PCGI_NAME=Zope
PCGI_MODULE_PATH=%(ZOPE_HOME)s/lib/python/Zope
PCGI_PUBLISHER=%(ZOPE_HOME)s/pcgi/pcgi_publisher.py
PCGI_EXE=%(PYTHON)s
PCGI_SOCKET_FILE=%(HERE)s/var/pcgi.soc
PCGI_PID_FILE=%(HERE)s/var/pcgi.pid
PCGI_ERROR_LOG=%(HERE)s/var/pcgi.log
PCGI_DISPLAY_ERRORS=1
BOBO_REALM=Zope
BOBO_DEBUG_MODE=1
INSTANCE_HOME=%(HERE)s
''' % globals())
    
def zctl_do(args):
    """Execute python commands"""
    if ZEO:
        start_zeo([])
    for k,v in ZOPE_ENV.items():
        env[k] = str(v)
    os.chdir(pjoin(ZOPE_HOME, 'lib', 'python'))
    msg = """
          Zope debugging session for %s
          The root application object is bound to name 'app'.
          To let other people see your changes, you must:
            get_transaction().commit()
          To see other people's changes, you must:
            app._p_jar.sync()""" % HERE
    options = "-c"
    if not args or '-i' in args:
        options = '-i ' + options
        if args:
            args.remove('-i')
        print msg
    while '-f' in args:
        fpos = args.index('-f')
        args.pop(fpos)
        args[fpos] = 'execfile("%s");' % args[fpos]
    cmd = ("%s %s 'import ZServer, Zope; app=Zope.app(); %s'"
           % (PYTHON, options, string.join(args, " ")))
    run(cmd)

def zctl_debug(args):
    """Start an interactive debugging session"""
    args.insert(0, '-i')
    zctl_do(args)

def zctl_script(args):
    """Execute a Python script"""
    args[0] = os.path.abspath(args[0])
    args.insert(0, '-f')
    zctl_do(args)

def zctl_test(args):
    """Run a test"""
    zctl_script(args)

# Internal helper functions

def _check_for_service(host, port):
    """Return 1 if server is found at (host, port), 0 otherwise."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(host, int(port))
        return 1
    except socket.error:
        return 0

def _dispatch():
    """Dispatch command line invocation."""
    if len(sys.argv) == 1:
        print """\
    start [confname ...] [--zeo -arg ... [--zope]] -arg ...
    stop [confname ...]
    stop_all
    start_zeo
    stop_zeo
    status [confname ...]
    make_cgi [filename]
    debug
    test filename
    do [-i] [-f filename]* commands
    script filename
"""
        args = string.split(raw_input('command: '))
    else:
        args = sys.argv[1:]
    action = string.lower(args.pop(0))
    if not globals().has_key('zctl_'+action):
        print 'Unknown command "%s"' % action
        sys.exit(1)
    globals()['zctl_'+action](args)

if __name__ == "__main__":
    _dispatch()
