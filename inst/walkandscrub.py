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

import os, sys
DEBUG = 0
if os.name in ('posix', 'nt', 'dos'):
    EXCLUDED_NAMES=['..', '.']
else:
    EXCLUDED_NAMES=[]

# extend EXCLUDED_NAMES here manually with filenames ala "asyncore.pyc" for
# files that are only distributed in compiled format (.pyc, .pyo)
# if necessary (not currently necessary in 2.3.1 AFAIK) - chrism

def walkandscrub(path):
    path = os.path.expandvars(os.path.expanduser(path))
    print
    print '-'*78
    sys.stdout.write(
        "Deleting '.pyc' and '.pyo' files recursively under %s...\n" % path
        )
    os.path.walk(path, scrub, [])
    sys.stdout.write('Done.\n')

def scrub(list, dirname, filelist):
    for name in filelist:
        if name in EXCLUDED_NAMES:
            continue
        prefix, ext = os.path.splitext(name)
        if ext == '.pyo' or ext == '.pyc':
            full = os.path.join(dirname, name)
            os.unlink(full)
            filelist.remove(name)
            if DEBUG: print full
            
if __name__ == '__main__':
    DEBUG = 1
    walkandscrub(os.getcwd())
