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
"""Shared routines used by the various scripts.

"""
import os, sys, string

try: import thread
except:
    print "*******************************************"
    print "Error: "
    print "Zope requires Python thread support!"
    print "*******************************************"
    sys.exit(1)

cd=os.chdir

def do(command, picky=1, quiet=0):
    if not quiet:
        print command
    i=os.system(command)
    if i and picky: raise SystemError, i

def wheres_Makefile_pre_in():
    "Identify Makefile.pre.in location (in much the same way it does)."
    return "%s/lib/python%s/config/Makefile.pre.in" % (sys.exec_prefix,
                                                       sys.version[:3])

def error(message, error):
    print message
    if error: print "%s: %s" % error[:2]

def ch(path, user, group, mode=0600, quiet=0):
    if group:
        mode=mode|060
        do("chgrp %s %s" % (group, path), 0, quiet)

    if user:
        do("chown %s %s" % (user, path), 0, quiet)

    do("chmod %s %s" % (oct(mode), path), 0, quiet)
    

def make(*args):
    print
    print '-'*48
    print 'Compiling extensions in %s' % string.join(args,'/')
    
    for a in args: os.chdir(a)
    # Copy over and use the prototype extensions makefile from python dist:
    do("cp %s ." % wheres_Makefile_pre_in())
    do('make -f Makefile.pre.in boot PYTHON=%s' % sys.executable)
    do('make')
    do('make clean')
    for a in args: os.chdir('..')
