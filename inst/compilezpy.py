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

import compileall, os, sys

class Shutup:
    def write(*args): pass # :)

class NoteErr:
    wrote = 0
    def write(self, *args):
        self.wrote = 1
        apply(stderr.write, args)

print
print '-'*78
print 'Compiling python modules'
stdout = sys.stdout
stderr = sys.stderr
try:
    try:
        success = 0
        sys.stdout = Shutup()
        sys.stderr = NoteErr()
        success = compileall.compile_dir(os.getcwd())
    finally:
        success = success and not sys.stderr.wrote
        sys.stdout = stdout
        sys.stderr = stderr
except:
    success = 0
    import traceback
    traceback.print_exc()
    
if not success:
    print
    print '!' * 78
    print 'There were errors during Python module compilation.'
    print '!' * 78
    print
    sys.exit(1)
