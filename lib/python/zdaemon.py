#!/usr/bin/env python
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
"""

zinit, slightly smarter server manager and ZServer startup script.

  zinit will:

    - Fork a parent and a child

    - restart the child if it dies

    - write a pid file so you can kill (the parent)

    - reports the childs pid to stdout so you can kill that too

TODO

  - Have the parent reap the children when it dies

  - etc.

"""

import os, sys, time, signal, posix

pyth = sys.executable

class KidDiedOnMeError(Exception):
    pass

class ExecError(Exception):
    pass

class ForkError(Exception):
    pass

FORK_ATTEMPTS = 2

# This is the number of seconds between the parent pulsing the child.
# Set to 0 to deactivate pulsing.

BEAT_DELAY = 0
VERBOSE = 1

# If you want the parent to 'pulse' Zope every 'BEAT_DELAY' seconds,
# put the URL to the method you want to call here.  This can be any
# methodish object that can be called through the web.  Format is:
#
# activities = (("http://x/method", "username", "password"),)
#
# username and password may be None if the method does not require
# authentication. 

# activities = (('http://localhost:9222/Heart/heart', 'michel', '123'),
#               )

import zLOG

#this is a bit of a hack so I dont have to change too much code
def pstamp(message, sev):
    zLOG.LOG("zdaemon", sev,
             ("zdaemon: %s: %s" % (time.ctime(time.time()), message)))

def heartbeat():
    print 'tha-thump'
    if activities:
        for a in activities:
            try:
                result = ZPublisher.Client.call(a[0], a[1], a[2])
            except:
                pstamp('activity %s failed!' % a[0], zLOG.WARNING)
                return

            if result and VERBOSE:
                pstamp('activity %s returned: %s' % (a[0], result),
                       zLOG.BLATHER)


def forkit(attempts = FORK_ATTEMPTS):
    while attempts:
        # if at first you don't succeed...
        attempts = attempts - 1
        try:
            pid = os.fork()
        except os.error:
            pstamp('Houston, the fork failed', zLOG.ERROR)
            time.sleep(2)
        else:
            pstamp('Houston, we have forked', zLOG.INFO)
            return pid

def run(argv, pidfile=''):
    if os.environ.has_key('ZDAEMON_MANAGED'):
        # We're the child at this point.  Don't ask. :/
        return
    
    os.environ['ZDAEMON_MANAGED']='TRUE'
    
    if not os.environ.has_key('Z_DEBUG_MODE'):
        # Detach from terminal
        pid = os.fork()
        if pid:
            sys.exit(0)
        posix.setsid()

    while 1:

        try:
            pid = forkit()

            if pid is None:
                raise ForkError

            elif pid:
                # Parent 
                pstamp(('Hi, I just forked off a kid: %s' % pid), zLOG.INFO)
                # here we want the pid of the parent
                if pidfile:
                    pf = open(pidfile, 'w+')
                    pf.write(("%s" % os.getpid()))
                    pf.close()

                while 1: 
                    if not BEAT_DELAY:
                        p,s = os.waitpid(pid, 0)
                    else:
                        p,s = os.waitpid(pid, os.WNOHANG)
                        if not p:
                            time.sleep(BEAT_DELAY)
                            heartbeat()
                            continue
                    if s:
                        pstamp(('Aiieee! %s exited with error code: %s' 
                                % (p, s)), zLOG.ERROR)
                    else:
                        pstamp(('The kid, %s, died on me.' % pid),
                               zLOG.WARNING)
                        raise ForkError

                    raise KidDiedOnMeError

            else:
                # Child
                os.execv(pyth, (pyth,)+tuple(argv))
                

        except ExecError:
            sys.exit()
        except ForkError:
            sys.exit()
        except KidDiedOnMeError:
            pass

def main():
    argv=sys.argv[1:]
    if argv and argv[0][:2]=='-p':
        pidf=argv[0][2:]
        del argv[0]
    else:
        pidf=''

    if not argv:
        print __doc__ % vars()
        print
        print 'Error: no script given'
            
    run(argv, pidf)
    

if __name__ == '__main__': main()







