##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import os
import sys

def main(dirname):
    os.path.walk(dirname, rmpycs, None)

def rmpycs(arg, dirname, names):
    for name in names:
        path = os.path.join(dirname, name)
        if ( name.endswith('.pyc') or name.endswith('.pyo') and
             os.path.isfile(path) ):
            os.unlink(path)

if __name__ == '__main__':
    main(sys.argv[1])
