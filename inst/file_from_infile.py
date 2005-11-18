##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
Reads a file named by 'src', performs textual replacements on the
file based on sed-style markup, and writes the result to the file named
by 'dst' unless 'dst' already exists.
"""
import getopt, os, sys
from os.path import abspath, split, dirname
import shutil
import versions

default_map = {
    'PYTHON'              : sys.executable,
    'BASE_DIR'            : abspath(split(dirname(sys.argv[0]))[0]),
    'ZOPE_MAJOR_VERSION'  : versions.ZOPE_MAJOR_VERSION,
    'ZOPE_MINOR_VERSION'  : versions.ZOPE_MINOR_VERSION,
    'ZOPE_BRANCH_NAME'    : versions.ZOPE_BRANCH_NAME,
    'VERSION_RELEASE_TAG' : versions.VERSION_RELEASE_TAG,
    }

def main(source, dest, map, force):
    if not force and os.path.exists(dest):
        print '%s exists, so I left it alone' % dest
    else:
        txt = open(source, 'rb').read()
        for k, v in map.items():
            txt = txt.replace('<<%s>>' % k, v)
        outfile = open(dest, 'wb')
        outfile.write(txt)
        outfile.close()
        shutil.copystat(source, dest)
        print "Wrote %s from %s" % (dest, source)

def usage():
    print "%s [opts] src dst" % sys.argv[0]
    print
    print "Reads a file named by 'src', performs textual replacements on "
    print "the file based on sed-style markup embedded in the infile, and "
    print "and writes the result to the file named by 'dst' unless 'dst'."
    print "already exists.  The generated file will have the same permissions"
    print "and other mode bit settings as the source file."
    print
    print "Options:"
    print
    print "  --force      Force replacement of dst even if it already exists."
    for name, value in default_map.items():
        print ("  --%s=value     controls text replacement, default '%s'"
               % (name, value))

if __name__ == '__main__':
    if len(sys.argv) < 3:
        usage()
        sys.exit(127)
    map = default_map.copy()
    force = 0
    try:
        longopts = ['help', 'force']
        for name in default_map.keys():
            longopts.append('%s=' % name)
        opts, args = getopt.getopt(sys.argv[1:], 'h', longopts)
    except getopt.GetoptError, v:
        print v
        usage()
        sys.exit(1)
    try:
        source, dest = args
    except:
        usage()
        sys.exit(1)
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
        if o == '--force':
            force = 1
        if o in map.keys():
            map[o] = a
    main(source, dest, map, force)

