#!/usr/local/bin/python1.5.1
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

import os, sys, time, signal

SOFTWARE_HOME = '/projects/users/zmichel'
START_FILE = os.path.join(SOFTWARE_HOME, 'ZServer', 'start.py')
pyth = sys.executable

sys.path.insert(0,os.path.join(SOFTWARE_HOME,'lib','python'))

import ZPublisher.Client

class KidDiedOnMeError:
    pass

class ExecError:
    pass

class ForkError:
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


def pstamp(message):
    print "zinit: %s: %s" % (time.ctime(time.time()), message)

def heartbeat():
    print 'tha-thump'
    if activities:
        for a in activities:
            try:
                result = ZPublisher.Client.call(a[0], a[1], a[2])
            except:
                pstamp('activity %s failed!' % a[0])
                return

            if result and VERBOSE:
                pstamp('activity %s returned: %s' % (a[0], result))


def forkit(attempts = FORK_ATTEMPTS):
    while attempts:
        # if at first you don't succeed...
        attempts = attempts + 1
        try:
            pid = os.fork()
        except os.error:
            pstamp('Houston, the fork failed')
            time.sleep(2)
        else:
            pstamp('Houston, we have forked')
            return pid

def main():
    while 1:
        try:
            pid = forkit()

            if pid is None:
                raise ForkError

            elif pid:
                # Parent 
                pstamp(('Hi, I just forked off a kid: %s' % pid))
                # here we want the pid of the parent
                pf = open(os.path.join(SOFTWARE_HOME, 'var', 
                                       'ZServerManager.pid'), 'w+')
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
                                % (p, s)))
                    else:
                        pstamp(('The kid, %s, died on me.' % pid))

                    raise KidDiedOnMeError

            else:
                # Child
                try:
                    os.execv(START_FILE, ())
                except:
                    raise ExecError
                os._exit(0)

        except ExecError:
            sys.exit()
        except ForkError:
            sys.exit()
        except KidDiedOnMeError:
            pass

if __name__ == '__main__':

    main()







