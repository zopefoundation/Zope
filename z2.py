##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""Zope 2 ZServer start-up file

Usage: %(program)s [options] [environment settings]

Options:

  -h

    Output this text.

  -z path

    The location of the Zope installation.
    The default is the location of this script, %(here)s.

  -Z path

    Unix only! This option is ignored on windows.

    If this option is specified, a separate managemnt process will
    be created that restarts Zope after a shutdown (or crash).
    The path must point to a pid file that the process will record its
    process id in. The path may be relative, in which case it will be
    relative to the Zope location.

  -t n

    The number of threads to use, if ZODB3 is used. The default is
    %(NUMBER_OF_THREADS)s.

  -D

    Run in Zope debug mode.  This is equivalent to
    supplying the environment variable setting Z_DEBUG_MODE=1

  -a ipaddress

    The IP address to listen on.  If this is an empty string, then all
    addresses on the machine are used. The default is %(IP_ADDRESS)s.

  -d ipaddress

    IP address of your DNS server. If this is an empty string, then
    IP addresses will not be logged. If you have DNS service on your
    local machine then you can set this to 127.0.0.1.
    The default is: %(DNS_IP)s.
    
  -u username or uid number
  
    The username to run ZServer as. You may want to run ZServer as 'nobody'
    or some other user with limited resouces. The only works under Unix, and
    if ZServer is started by root. The default is: %(UID)s

  -P number

    Set the web, ftp and monitor port numbers simultaneously
    as offsets from the number.  The web port number will be number+80.
    The FTP port number will be number+21.  The monitoe port number will
    be number+99.
    
  -w port
  
    The Web server (HTTP) port.  This defaults to %(HTTP_PORT)s. The
    standard port for HTTP services is 80.  If this is an empty
    string, then HTTP is disabled.

  -f port
  
    The FTP port.  If this is an empty string, then FTP is disabled.
    The standard port for FTP services is 21.  The default is %(FTP_PORT)s.

  -p path

    Path to the PCGI resource file.  The default value is
    %(PCGI_FILE)s, relative to the Zope location.  If this is an empty
    string or the file does not exist, then PCGI is disabled.

  -m port
  
    The secure monitor server port. If this is an empty string, then the
    monitor server is disabled. The monitor server allows interactive
    Python style access to a running ZServer. To access the server see
    medusa/monitor_client.py or medusa/monitor_client_win32.py. The monitor
    server password is the same as the Zope super manager password set in
    the 'access' file. The default is %(MONITOR_PORT)s.

  -2

    Use ZODB 2 (aka BoboPOS) rather than ZODB 3

  -l path

    Path to the ZServer log file. If this is a relative path then the
    log file will be written to the 'var' directory. The default is
    %(LOG_FILE)s. 

Environment settings are of the form: NAME=VALUE.

Note: you *must* use Python 1.5.2 or later!
"""
import os, sys, getopt, string

program=sys.argv[0]
here=os.path.join(os.getcwd(), os.path.split(program)[0])
Zpid=''

########################################################################
# Configuration section

## General configuration options
##

# If you want run as a daemon, then uncomment the line below:
if sys.platform=='win32': Zpid=''
else: Zpid='var/zProcessManager.pid'

# This is the IP address of the network interface you want your servers to
# be visible from.  This can be changed to '' to listen on all interfaces.
IP_ADDRESS=''

# IP address of your DNS server. Set to '' if you do not want to resolve
# IP addresses. If you have DNS service on your local machine then you can
# set this to '127.0.0.1'
DNS_IP=''

# User id to run ZServer as. Note that this only works under Unix, and if
# ZServer is started by root.
UID='nobody'

# Log file location. If this is a relative path, then it is joined the
# the 'var' directory.
LOG_FILE='Z2.log'

## HTTP configuration
##

# Port for HTTP Server. The standard port for HTTP services is 80.
HTTP_PORT=9673

# HTTP enivornment settings.
HTTP_ENV={}

## FTP configuration

# Port for the FTP Server. The standard port for FTP services is 21.
FTP_PORT=9221

## PCGI configuration

# You can configure the PCGI server manually, or have it read its
# configuration information from a PCGI info file.
PCGI_FILE='Zope.cgi'

## Monitor configuration
MONITOR_PORT=9999

# Module to be published, which must be Main or Zope
MODULE='Zope'

# The size of the thread pool, if ZODB3 is used.
NUMBER_OF_THREADS=4

#
########################################################################

########################################################################
# Handle command-line arguments:

try:
    if string.split(sys.version)[0] < '1.5.2':
        raise 'Invalid python version', string.split(sys.version)[0]
    
    opts, args = getopt.getopt(sys.argv[1:], 'hz:Z:t:a:d:u:w:f:p:m:l:2DP:')

    # Get environment variables
    for a in args:
        if string.find(a,'='):
            a=string.split(a,'=')
            o=a[0]
            v=string.join(a[1:],'=')
            if o: 
              os.environ[o]=v
              HTTP_ENV[o]=v
        else:
            raise 'Invalid argument', a

    for o, v in opts:
        if o=='-z': here=v
        elif o=='-Z': Zpid=v
        elif o=='-t':
            try: v=string.atoi(v)
            except: raise 'Invalid number of threads', v
            NUMBER_OF_THREADS=v
        elif o=='-a': IP_ADDRESS=v
        elif o=='-d': DNS_IP=v
        elif o=='-u': UID=v
        elif o=='-D': os.environ['Z_DEBUG_MODE']='1'
        elif o=='-m':
            if v:
                try: 
                    v=string.atoi(v)
                    if v < 1: raise 'Invalid port', v
                except: raise 'Invalid port', v
            MONITOR_PORT=v
        elif o=='-w':
            if v:
                try: 
                    v=string.atoi(v)
                    if v < 1: raise 'Invalid port', v
                except: raise 'Invalid port', v
            HTTP_PORT=v
        elif o=='-f':
            if v:
                try:
                    v=string.atoi(v)
                    if v < 1: raise 'Invalid port', v
                except: raise 'Invalid port', v
            FTP_PORT=v
        elif o=='-P':
            if v:
                try:
                    v=string.atoi(v)
                    if v < 1: raise 'Invalid port', v
                except: raise 'Invalid port', v
            FTP_PORT=v+21
            HTTP_PORT=v+80
            MONITOR_PORT=v+99
        elif o=='-p': PCGI_FILE=v
        elif o=='-h':
            print __doc__ % vars()
            sys.exit(0)
        elif o=='-2': MODULE='Main'
        elif o=='-l': LOG_FILE=v


except SystemExit: sys.exit(0)
except:
    print __doc__ % vars()
    print
    print 'Error:'
    print "%s: %s" % (sys.exc_type, sys.exc_value)
    sys.exit(1)

if sys.platform=='win32': Zpid=''

#
########################################################################

########################################################################
# OK, let's get going!

# Jigger path:
sys.path=[os.path.join(here,'lib','python'),here
          ]+filter(None, sys.path)


# from this point forward we can use the zope logger

import zLOG, posix


if Zpid:
    import zdaemon, App.FindHomes 
    sys.ZMANAGED=1
    
    x = os.fork()
    if x:
        sys.exit(0)
    elif x == -1:
        zLOG.LOG("z2", zLOG.ERROR, "couldn't fork to detatch")
        sys.exit(1)
    pgrp = posix.setsid()
    if pgrp == -1:
        zLOG.LOG("z2", zLOG.ERROR, "setsid failed")
        sys.exit(1)

    zdaemon.run(sys.argv, os.path.join(INSTANCE_HOME, Zpid))

# Import Zope (or Main), and thus get SOFTWARE_HOME and INSTANCE_HOME
exec "import "+MODULE in {}

# Location of the ZServer log file. This file logs all ZServer activity.
# You may wish to create different logs for different servers. See
# medusa/logger.py for more information.
if not os.path.isabs(LOG_FILE):
    LOG_PATH=os.path.join(INSTANCE_HOME, 'var', LOG_FILE)
else:
    LOG_PATH=LOG_FILE

# Location of the ZServer pid file. When ZServer starts up it will write
# its PID to this file.
PID_FILE=os.path.join(INSTANCE_HOME, 'var', 'Z2.pid')


# import ZServer stuff

# First, we need to increase the number of threads
if MODULE=='Zope':
    from ZServer import setNumberOfThreads
    setNumberOfThreads(NUMBER_OF_THREADS)

from ZServer import resolver, logger, asyncore
from ZServer import zhttp_server, zhttp_handler, PCGIServer,FTPServer
from ZServer import secure_monitor_server

## ZServer startup
##

# Resolver and Logger, used by other servers
if DNS_IP:
    rs = resolver.caching_resolver(DNS_IP)
else:
    rs=None
lg = logger.file_logger(LOG_PATH)

# HTTP Server
if HTTP_PORT:
    hs = zhttp_server(
        ip=IP_ADDRESS,
        port=HTTP_PORT,
        resolver=rs,
        logger_object=lg)

    # Handler for a published module. zhttp_handler takes 3 arguments:
    # The name of the module to publish, and optionally the URI base
    # which is basically the SCIRPT_NAME, and optionally a dictionary
    # with CGI environment variables which override default
    # settings. The URI base setting is useful when you want to
    # publish more than one module with the same HTTP server. The CGI
    # environment setting is useful when you want to proxy requests
    # from another web server to ZServer, and would like the CGI
    # environment to reflect the CGI environment of the other web
    # server.    
    zh = zhttp_handler(MODULE, '', HTTP_ENV)
    hs.install_handler(zh)


# FTP Server
if FTP_PORT:
    zftp = FTPServer(
        module=MODULE,
        port=FTP_PORT,
        resolver=rs,
        logger_object=lg)

# PCGI Server
if PCGI_FILE:
    PCGI_FILE=os.path.join(here, PCGI_FILE)
    if os.path.exists(PCGI_FILE):
        zpcgi = PCGIServer(
            module=MODULE,
            ip=IP_ADDRESS,
            pcgi_file=PCGI_FILE,
            resolver=rs,
            logger_object=lg)

# Monitor Server
if MONITOR_PORT:
    from AccessControl.User import super
    monitor=secure_monitor_server(
        password=super._getPassword(),
        hostname=IP_ADDRESS,
        port=MONITOR_PORT)

# Try to set uid to server's uid. 
# This will only work if this script is run by root.
try:
    import pwd
    try:
        try:
            uid=string.atoi(UID)
        except:
            pass
        if type(UID) == type(""):
            uid = pwd.getpwnam(UID)[2]
        os.setuid(uid)
    except KeyError:
        zLOG.LOG("z2", zLOG.ERROR, ("can't find UID %s" % UID))
    
except:
    pass


# if it hasn't failed at this point, create a .pid file.
pf = open(PID_FILE, 'w')
pf.write(str(os.getpid()))
pf.close()

# Start Medusa, Ye Hass!
sys.ZServerExitCode=0
asyncore.loop()
sys.exit(sys.ZServerExitCode)








