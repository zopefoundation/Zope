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
Yes, this is cheesy.

"""

import sys, os
if not (sys.version >= "2.2" and sys.version_info >= (2, 2, 2)):
    raise RuntimeError, "Python 2.2.2 or later is required"

def setup(me):
    home=os.path.split(me)[0]
    if not home or home=='.': home=os.getcwd()
    sys.path.insert(0, os.path.join(home,'inst'))
    sys.path.insert(0, home)
    return home

def main(me):
    home=setup(me)

    import build_pcgi
    user=group=''
    pcgi=os.path.join(home, 'Zope.cgi')
    import make_resource; make_resource.main(home, pcgi, user, group)
    os.chdir(home) # Just making sure
    import wo_pcgi; wo_pcgi.main(me)

if __name__=='__main__': main(sys.argv[0])
