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
"""Build a PCGI resource file.

You must be in the directory containing this script.
"""

import os
from do import *

def main(cwd=os.getcwd(), name='Zope', user='', group=''):
    python=sys.executable
    print '-'*78
    print 'Writing the pcgi resource file (ie cgi script), %s' % name
    cwd=os.environ.get('ZDIR',cwd)

    open(name,'w').write('''#!%(cwd)s/pcgi/pcgi-wrapper
PCGI_NAME=Zope
PCGI_MODULE_PATH=%(cwd)s/lib/python/Zope
PCGI_PUBLISHER=%(cwd)s/pcgi/pcgi_publisher.py
PCGI_EXE=%(python)s
PCGI_SOCKET_FILE=%(cwd)s/var/pcgi.soc
PCGI_PID_FILE=%(cwd)s/var/pcgi.pid
PCGI_ERROR_LOG=%(cwd)s/var/pcgi.log
PCGI_DISPLAY_ERRORS=1
BOBO_REALM=%(name)s
BOBO_DEBUG_MODE=1
INSTANCE_HOME=%(cwd)s
''' % vars())

    ch(name, user, group, 0755)
    
