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
"""Try to do all of the installation steps.

This must be run from the top-level directory of the installation.
\(Yes, this is cheezy.  We'll fix this when we have a chance.)

"""

import sys, os, getopt
from do import *

def setup(me):
    home=os.path.split(me)[0]
    if not home or home=='.': home=os.getcwd()
    home=os.path.split(home)[0]
    if not home or home=='.': home=os.getcwd()
    sys.path.insert(0, os.path.join(home))
    sys.path.insert(0, os.path.join(home,'inst'))
    return home

def main(args):
    me=args[0]
    home=setup(me)
    pcgi=os.path.join(home, 'Zope.cgi')
    usage="""install [options]

    where options are:

       -p   -- Supply the path to the PCGI resource file.
               This defaults to %s.
               Note that this path must include the file name.
    
       -g   -- Supply the name of the unix group to which
               the user that runs your web server belongs.
               If not specified, the installer will attempt
               to determine the group itself. If no group
               is specified and the installer is unable to
               determine the group, the install will fail.
    
       -u   -- Supply the name of the unix user used to
               run your web server. If not specified, this
               defaults to the userid of the current user,
               or 'nobody' is the current user is root.
    
       -h   -- Show command summary
    """ % (pcgi)
    
    try: options, args = getopt.getopt(sys.argv[1:], 'p:g:hu:')
    except: error(usage, sys.exc_info())
    if args: error('', ('Unexpected arguments', args))

    group=user=''
    for k, v in options:
        if k=='-p': pcgi=v
        elif k=='-g': group=v
        elif k=='-u': user=v
        elif k=='-h':
            print usage
            sys.exit()

    import compilezpy
    print '-'*78
    import zpasswd; zpasswd.write_inituser(home, user, group)
    import default_content; default_content.main(home, user, group)
    import make_resource; make_resource.main(home, pcgi, user, group)
    import make_start; make_start.sh(home, user, group)

    print '-'*78
    print
    print 'Done!'

if __name__=='__main__': main(sys.argv)
