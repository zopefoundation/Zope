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
#
#	Author: Sam Rushing <rushing@nightmare.com>
#

"""socket interface to unix syslog.
On Unix, there are usually two ways of getting to syslog: via a
local unix-domain socket, or via the TCP service.

Usually "/dev/log" is the unix domain socket.  This may be different
for other systems.

>>> my_client = syslog_client ('/dev/log')

Otherwise, just use the UDP version, port 514.

>>> my_client = syslog_client (('my_log_host', 514))

On win32, you will have to use the UDP version.  Note that
you can use this to log to other hosts (and indeed, multiple
hosts).

This module is not a drop-in replacement for the python
<syslog> extension module - the interface is different.

Usage:

>>> c = syslog_client()
>>> c = syslog_client ('/strange/non_standard_log_location')
>>> c = syslog_client (('other_host.com', 514))
>>> c.log ('testing', facility='local0', priority='debug')

"""

# TODO: support named-pipe syslog.
# [see ftp://sunsite.unc.edu/pub/Linux/system/Daemons/syslog-fifo.tar.z]

# from <linux/sys/syslog.h>:
# ===========================================================================
# priorities/facilities are encoded into a single 32-bit quantity, where the
# bottom 3 bits are the priority (0-7) and the top 28 bits are the facility
# (0-big number).  Both the priorities and the facilities map roughly
# one-to-one to strings in the syslogd(8) source code.  This mapping is
# included in this file.
#
# priorities (these are ordered)

LOG_EMERG       = 0     #  system is unusable 
LOG_ALERT       = 1     #  action must be taken immediately 
LOG_CRIT        = 2     #  critical conditions 
LOG_ERR         = 3     #  error conditions 
LOG_WARNING     = 4     #  warning conditions 
LOG_NOTICE      = 5     #  normal but significant condition 
LOG_INFO        = 6     #  informational 
LOG_DEBUG       = 7     #  debug-level messages 

#  facility codes 
LOG_KERN        = 0     #  kernel messages 
LOG_USER        = 1     #  random user-level messages 
LOG_MAIL        = 2     #  mail system 
LOG_DAEMON      = 3     #  system daemons 
LOG_AUTH        = 4     #  security/authorization messages 
LOG_SYSLOG      = 5     #  messages generated internally by syslogd 
LOG_LPR         = 6     #  line printer subsystem 
LOG_NEWS        = 7     #  network news subsystem 
LOG_UUCP        = 8     #  UUCP subsystem 
LOG_CRON        = 9     #  clock daemon 
LOG_AUTHPRIV    = 10    #  security/authorization messages (private) 

#  other codes through 15 reserved for system use 
LOG_LOCAL0      = 16        #  reserved for local use 
LOG_LOCAL1      = 17        #  reserved for local use 
LOG_LOCAL2      = 18        #  reserved for local use 
LOG_LOCAL3      = 19        #  reserved for local use 
LOG_LOCAL4      = 20        #  reserved for local use 
LOG_LOCAL5      = 21        #  reserved for local use 
LOG_LOCAL6      = 22        #  reserved for local use 
LOG_LOCAL7      = 23        #  reserved for local use 

priority_names = {
    "alert":    LOG_ALERT,
    "crit":     LOG_CRIT,
    "debug":    LOG_DEBUG,
    "emerg":    LOG_EMERG,
    "err":      LOG_ERR,
    "error":    LOG_ERR,        #  DEPRECATED 
    "info":     LOG_INFO,
    "notice":   LOG_NOTICE,
    "panic":    LOG_EMERG,      #  DEPRECATED 
    "warn":     LOG_WARNING,        #  DEPRECATED 
    "warning":  LOG_WARNING,
    }

facility_names = {
    "auth":     LOG_AUTH,
    "authpriv": LOG_AUTHPRIV,
    "cron":     LOG_CRON,
    "daemon":   LOG_DAEMON,
    "kern":     LOG_KERN,
    "lpr":      LOG_LPR,
    "mail":     LOG_MAIL,
    "news":     LOG_NEWS,
    "security": LOG_AUTH,       #  DEPRECATED 
    "syslog":   LOG_SYSLOG,
    "user":     LOG_USER,
    "uucp":     LOG_UUCP,
    "local0":   LOG_LOCAL0,
    "local1":   LOG_LOCAL1,
    "local2":   LOG_LOCAL2,
    "local3":   LOG_LOCAL3,
    "local4":   LOG_LOCAL4,
    "local5":   LOG_LOCAL5,
    "local6":   LOG_LOCAL6,
    "local7":   LOG_LOCAL7,
    }

import socket

class syslog_client:
    def __init__ (self, address='/dev/log'):
        self.address = address
        if type (address) == type(''):
            try: # APUE 13.4.2 specifes /dev/log as datagram socket
                self.socket = socket.socket( socket.AF_UNIX
                                                       , socket.SOCK_DGRAM)
                self.socket.connect (address)
            except: # older linux may create as stream socket
                self.socket = socket.socket( socket.AF_UNIX
                                                       , socket.SOCK_STREAM)
                self.socket.connect (address)
            self.unix = 1
        else:
            self.socket = socket.socket( socket.AF_INET
                                                   , socket.SOCK_DGRAM)
            self.unix = 0

    # curious: when talking to the unix-domain '/dev/log' socket, a
    #   zero-terminator seems to be required.  this string is placed
    #   into a class variable so that it can be overridden if
    #   necessary.

    log_format_string = '<%d>%s\000'

    def log (self, message, facility=LOG_USER, priority=LOG_INFO):
        message = self.log_format_string % (
            self.encode_priority (facility, priority),
            message
            )
        if self.unix:
            self.socket.send (message)
        else:
            self.socket.sendto (message, self.address)

    def encode_priority (self, facility, priority):
        if type(facility) == type(''):
            facility = facility_names[facility]
        if type(priority) == type(''):
            priority = priority_names[priority]         
        return (facility<<3) | priority

    def close (self):
        if self.unix:
            self.socket.close()

if __name__ == '__main__':
    """
       Unit test for syslog_client.  Set up for the test by:
    
    * tail -f /var/log/allstuf (to see the "normal" log messages).

        * Running the test_logger.py script with a junk file name (which
      will be opened as a Unix-domain socket). "Custom" log messages
      will go here.

    * Run this script, passing the same junk file name.

    * Check that the "bogus" test throws, and that none of the rest do.

    * Check that the 'default' and 'UDP' messages show up in the tail.

    * Check that the 'non-std' message shows up in the test_logger
      console.

    * Finally, kill off the tail and test_logger, and clean up the
      socket file.
    """
    import sys, traceback

    if len( sys.argv ) != 2:
       print "Usage: syslog.py localSocketFilename"
       sys.exit()

    def test_client( desc, address=None ):
        try:
            if address:
                client = syslog_client( address )
            else:
                client = syslog_client()
        except:
            print 'syslog_client() [%s] ctor threw' % desc
            traceback.print_exc()
            return

        try:
            client.log( 'testing syslog_client() [%s]' % desc
                      , facility='local0', priority='debug' )
            print 'syslog_client.log() [%s] did not throw' % desc
        except:
            print 'syslog_client.log() [%s] threw' % desc
            traceback.print_exc()

    test_client( 'default' )
    test_client( 'bogus file', '/some/bogus/logsocket' )
    test_client( 'nonstd file', sys.argv[1] )
    test_client( 'UDP',  ('localhost', 514) )
