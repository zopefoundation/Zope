##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import os
import sys

mydir = os.path.dirname(os.path.abspath(sys.argv[0]))
zopehome = os.path.dirname(mydir)
softwarehome = os.path.join(zopehome, "lib", "python")

if softwarehome not in sys.path:
    sys.path.insert(0, softwarehome)

from ZEO.mkzeoinst import ZEOInstanceBuilder

def main():
    ZEOInstanceBuilder().run()

if __name__ == "__main__":
    main()
