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

# Using PYTHONHOME is bad under Python 2.0
if sys.version[:1]=='2':
    varname='INST_HOME'
else:
    varname='PYTHONHOME'

def sh(home, user, group):
    start=os.path.join(home, 'start')
    if not os.path.exists(start):
        print '-'*78
        print 'Creating start script, start'
        open(start,'w').write(
            "#! /bin/sh\n"
            "reldir=`dirname $0`\n"
            "%s=`cd $reldir; pwd`\n"
            "export %s\n"
            'exec %s \\\n     $%s/z2.py \\\n     -D "$@"\n'
            % (varname, varname, sys.executable, varname))
        ch(start,user,group,0711)

    stop=os.path.join(home, 'stop')
    if not os.path.exists(stop):
        print '-'*78
        print 'Creating stop script, stop'
        open(stop,'w').write(
            "#! /bin/sh\n"
            "kill `cat %s`" 
            % os.path.join(home,'var','Z2.pid'))
        ch(stop,user,group,0711)

