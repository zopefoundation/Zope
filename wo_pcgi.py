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

import sys, os

def setup(me):
    home=os.path.split(me)[0]
    if not home or home=='.': home=os.getcwd()
    sys.path.insert(0, os.path.join(home,'inst'))
    return home

def main(me):
    home=setup(me)
    import walkandscrub
    walkandscrub.walkandscrub(home)
    import compilezpy
    import build_extensions
    build_extensions.build()
    user=group=''
    import default_content; default_content.main(home, user, group)

    pcgi=os.path.join(home, 'Zope.cgi')
    import make_start; make_start.sh(home, user, group)
    import zpasswd; zpasswd.write_inituser(home, user, group)

    print '-'*78
    print
    print 'Done!'

if __name__=='__main__': main(sys.argv[0])
