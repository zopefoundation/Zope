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

  h

    Output this text.

  z path

    The location of the Zope installation.
    The default is the location of this script, %(here)s.

  Z path

    Unix only! This option is ignored on windows.

    If this option is specified, a separate managemnt process will
    be created that restarts Zope after a shutdown (or crash).
    The path must point to a pid file that the process will record it's
    process id in. The path may be relative, in which case it will be
    relative to the Zope location.

  t n

    The number of threads to use, if ZODB3 is used. The default is
    %(NUMBER_OF_THREADS)s.

  a ipaddress

    The IP address to listen on.  If this is a empty string, then all
    addresses on the machine are used. The default is %(IP_ADDRESS)s.

  n hostname

    Host name of the server machine. You may use 'localhost' if your server 
    doesn't have a host name. The default is %(HOSTNAME)s.

  d ipaddress

    IP address of your DNS server. If you have DNS service on your
    local machine then you can set this to 127.0.0.1.
    The default is: %(DNS_IP)s.
    
  w port
  
    The Web server (HTTP) port.  This defaults to %(HTTP_PORT)s. The
    standard port for HTTP services is 80.  If this is an empty
    string, then HTTP is disabled.

  f port
  
    The FTP port.  If this is an empty string, then FTP is disabled.
    The standard port for FTP services is 21.  The default is %(FTP_PORT)s.

  p path

    Path to the PCGI resource file.  The default value is
    %(PCGI_FILE)s, relative to the Zope location.  If this is an empty
    string or the file does not exist, then PCGI is disabled.

  2

    Use ZODB 2 (aka BoboPOS) rather than ZODB 3

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

# If you want run as a deamon, then uncomment the line below:
if sys.platform=='win32': Zpid=''
else: Zpid='var/zProcessManager.pid'

# This is the IP address of the network interface you want your servers to
# be visible from.  This can be changed to '' to listen on all interfaces.
IP_ADDRESS=''

# Host name of the server machine. You may use 'localhost' if your server 
# doesn't have a host name.
HOSTNAME='localhost'

# IP address of your DNS server. If you have DNS service on your local machine
# then you can set this to '127.0.0.1'
DNS_IP='127.0.0.1'

## HTTP configuration
##

# Port for HTTP Server. The standard port for HTTP services is 80.
HTTP_PORT=9673

## FTP configuration
##

# Port for the FTP Server. The standard port for FTP services is 21.
FTP_PORT=9221

## PCGI configuration

# You can configure the PCGI server manually, or have it read its
# configuration information from a PCGI info file.
PCGI_FILE='Zope.cgi'

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
    
    opts, args = getopt.getopt(sys.argv[1:], 'hz:Z:t:a:n:d:w:f:p:2')

    # Get environment variables
    for a in args:
        if string.find(a,'='):
            a=string.split(a,'=')
            o=a[0]
            v=string.join(a[1:],'=')
            if o: os.environ[o]=v
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
        elif o=='-n': HOSTNAME=v
        elif o=='-d': DNS_IP=v
        elif o=='-w':
            if v:
                try: v=string.atoi(v)
                except: raise 'Invalid port', v
            HTTP_PORT=v
        elif o=='-f':
            if v:
                try: v=string.atoi(v)
                except: raise 'Invalid port', v
            FTP_PORT=v
        elif o=='-p': PCGI_FILE=v
        elif o=='-h':
            print __doc__ % vars()
            sys.exit(0)
        elif o=='-2': MODULE='Main'

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
sys.path=[os.path.join(here,'lib','python'),
          os.path.join(here,'ZServer'),
          ]+filter(None, sys.path)

if Zpid:
    import zdeamon, App.FindHomes 
    sys.ZMANAGED=1
    zdeamon.run(sys.argv, os.path.join(INSTANCE_HOME, Zpid))


# Import Zope (or Main), and thus get SOFTWARE_HOME and INSTANCE_HOME
exec "import "+MODULE in {}

# Location of the ZServer log file. This file logs all ZServer activity.
# You may wish to create different logs for different servers. See
# medusa/logger.py for more information.
LOG_FILE=os.path.join(INSTANCE_HOME, 'var', 'Z2.log')

# Location of the ZServer pid file. When ZServer starts up it will write
# its PID to this file.
PID_FILE=os.path.join(INSTANCE_HOME, 'var', 'Z2.pid')

# Try to become nobody. This will only work if this script is run by root.
try:
    import pwd
    try:
        nobody = pwd.getpwnam('nobody')[2]
    except pwd.error:
        nobody = 1 + max(map(lambda x: x[2], pwd.getpwall()))
    os.setuid(nobody)
except:
    pass

# open and close the log file, to make sure one is there.
v = open(LOG_FILE, 'a')
v.close()

# if it hasn't failed at this point, create a .pid file.
pf = open(PID_FILE, 'w')
pf.write(str(os.getpid()))
pf.close()


# import ZServer stuff

# First, we need to increase the number of threads
if MODULE=='Zope':
    import PubCore
    PubCore.setNumberOfThreads(NUMBER_OF_THREADS)

from medusa import resolver,logger,asyncore
from HTTPServer import zhttp_server, zhttp_handler
from PCGIServer import PCGIServer
from FTPServer import FTPServer

## ZServer startup
##

# Resolver and Logger, used by other servers
rs = resolver.caching_resolver(DNS_IP)
lg = logger.file_logger(LOG_FILE)

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
    zh = zhttp_handler(MODULE, '')
    hs.install_handler(zh)


# FTP Server
if FTP_PORT:
    zftp = FTPServer(
        module=MODULE,
        hostname=HOSTNAME,
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

# Start Medusa, Ye Hass!
sys.ZServerExitCode=0
asyncore.loop()
sys.exit(sys.ZServerExitCode)








