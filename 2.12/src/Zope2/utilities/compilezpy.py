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

import compileall, os, sys

class Shutup:
    def write(*args): pass # :)

class NoteErr:
    wrote = 0
    def write(self, *args):
        self.wrote = 1
        apply(stderr.write, args)

def compile_non_test(dir):
    """Byte-compile all modules except those in test directories."""
    success = compileall.compile_dir(dir, maxlevels=0)
    try:
        names = os.listdir(dir)
    except os.error:
        print "Can't list", dir
        names = []
    names.sort()
    for name in names:
        fullname = os.path.join(dir, name)
        if (name != os.curdir and name != os.pardir and
            os.path.isdir(fullname) and not os.path.islink(fullname) and
            name != 'test' and name != 'tests' and name != 'skins'):
            success = success and compile_non_test(fullname)
    return success

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
        success = compile_non_test(os.getcwd())
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
