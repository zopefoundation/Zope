##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import sys, os
from do import *

def sh(home, user, group):
    start=os.path.join(home, 'start')
    if not os.path.exists(start):
        print '-'*78
        print 'Creating start script, start'
        f = open(start,'w')
        f.write(START_SCRIPT % sys.executable)
        ch(start,user,group,0711)
        f.close()

    stop=os.path.join(home, 'stop')
    if not os.path.exists(stop):
        print '-'*78
        print 'Creating stop script, stop'
        f = open(stop,'w')
        f.write(STOP_SCRIPT % os.path.join(home,'var','Z2.pid'))
        ch(stop,user,group,0711)
        f.close()

START_SCRIPT="""#!/bin/sh
umask 077
reldir=`dirname $0`
cwd=`cd $reldir; pwd`
# Zope's event logger is controlled by the "EVENT_LOG_FILE" environment
# variable.  If you don't have a "EVENT_LOG_FILE" environment variable
# (or its older alias "STUPID_LOG_FILE") set, Zope will log to the standard
# output.  For more information on EVENT_LOG_FILE, see doc/ENVIRONMENT.txt.
ZLOGFILE=$EVENT_LOG_FILE
if [ -z "$ZLOGFILE" ]; then
        ZLOGFILE=$STUPID_LOG_FILE
fi
if [ -z "$ZLOGFILE" ]; then
        EVENT_LOG_FILE=""
        export EVENT_LOG_FILE
fi
exec %s $cwd/z2.py -D "$@"
"""

STOP_SCRIPT="#! /bin/sh\nkill `cat %s`\n"
