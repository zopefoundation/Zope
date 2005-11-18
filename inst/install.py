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
Generic file and directory installer.

Typically called when installing Zope via the Makefile written by
'configure.py' in the 'make install' step.
"""
import getopt
import os
import re
import shutil
import stat
import sys

# RE that, if a pathname's base name matches, causes it to be ignored
# when copying that file or directory.
default_omitpattern = r'(\..*|CVS|.*~)$'

def main(src, dst, dirmode=0755, fmode=0644,
         omitpattern=default_omitpattern, retain_xbit=1):
    """
    Copy a file or directory named by src to a file or directory named by
    dst, normalizing mode bit settings as necessary.  Recursively copies
    directory trees using shutil.copy2().

    Errors are reported to standard output.

      - 'dirmode' is the directory creation mode.  All directories
        are created with this mode.
      - 'fmode' is the default file creation mode.  This mode
        is modified by the status of the source file.  If the source
        file is executable, mod the fmode to be +wgo executable.
      - omitpattern is a Python-style regex pattern.  If a file
        or directory name matches this pattern, it will never be copied.
      - if the dst directory already exists, don't raise an error.
    """
    try:
        if os.path.isdir(src):
            copydir(src, dst, dirmode, fmode, omitpattern,
                    retain_xbit)
        else:
            names = omit([src], omitpattern)
            names and copyfile(names[0], dst, fmode, retain_xbit)

    except (IOError, os.error), why:
        print "Can't copy %s to %s: %s" % (`src`, `dst`, str(why))

def copydir(src, dst, dirmode, fmode, omitpattern, retain_xbit):
    names = omit(os.listdir(src), omitpattern)
    try:
        # always create directories with dirmode
        os.makedirs(dst, dirmode)
    except os.error, why:
        if why[0] == 17:
            # directory already exists
            pass
        else:
            raise
    for name in omit(names, omitpattern):
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        if os.path.isdir(srcname):
            copydir(srcname, dstname, dirmode,fmode,omitpattern,
                    retain_xbit)
        else:
            copyfile(srcname, dstname, fmode, retain_xbit)

def copylink(src, dst):
    linkto = os.readlink(src)
    os.symlink(linkto, dst)

def copyfile(src, dst, mode, retain_xbit):
    shutil.copy2(src, dst)
    # change dest file mode to fmode but
    # make +wgo executable if source file is executable
    dstmode = mode
    st = os.stat(src)
    srcmode = st[stat.ST_MODE]
    if retain_xbit and (srcmode & stat.S_IEXEC):
        dstmode = (mode | 0111)
    if os.path.isdir(dst):
        # if dst is a directory, copy the file in to it
        os.chmod(os.path.join(dst, os.path.split(src)[-1]), dstmode)
    else:
        os.chmod(dst, dstmode)

omitcache = {}

def omit(names, omitpattern):
    return [ n for n in names
             if not re.match(omitpattern, os.path.basename(n)) ]

def usage():
    print "%s [opts] source dest" % sys.argv[0]
    print
    print "Copies a file or directory specified by 'source' to 'dest'"
    print "normalizing mode bit settings as necessary."
    print
    print "If src is a file and dst is a directory, the file will be"
    print "copied into the dst directory.  However, if src is a directory"
    print "and dst is a directory, the contents of src will be copied into"
    print "dst."
    print
    print "opts: --dirmode=mode --fmode=mode --omitpattern=patt"
    print
    print "  --dontcopyxbit   when copying a file marked as executable,"
    print "                   don't make the copy executable."
    print "  --dirmode        mode bit settings of dest dirs (e.g. '755')"
    print "  --fmode          mode bit settings of dest files (e.g. '644')"
    print "                   (modified wgo+x when dontcopyxbit is not"
    print "                   specified)"
    print "  --omitpattern    a Python-style regex pattern.  File and"
    print "                   directory names which match this pattern will "
    print "                   not be copied.  The default omitpattern is"
    print "                   '%s'" % default_omitpattern

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "too few arguments"
        usage()
        sys.exit(2)
    dirmode = 0755
    fmode   = 0644
    omitpattern = default_omitpattern
    retain_xbit = 1
    longopts = ['dirmode=', 'fmode=', 'omitpattern=', 'help',
                'copyxmode' ]
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h', longopts)
    except getopt.GetoptError, v:
        print v
        usage()
        sys.exit(2)
    try:
        source, dest = args
    except:
        print "wrong number of arguments"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
        if o == '--dirmode':
            if not a.startswith('0'):
                a = '0%s' % a
            dirmode = eval(a)
        if o == '--fmode':
            if not a.startswith('0'):
                a = '0%s' % a
            fmode = eval(a)
        if o == '--omitpattern':
            omitpattern = a
        if o == '--dontcopyxbit':
            retain_xbit = 0
    main(source, dest, dirmode, fmode, omitpattern, retain_xbit)
