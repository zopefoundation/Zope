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
"""%(program)s:  Create a target directory from a skeleton directory.

usage:  %(program)s [options]

Options:
-h/--help -- print this help text
-s/--sourcedir -- the skeleton source directory
-t/--targetdir -- the directory to which the skeleton files will be copied
-u/--uid       -- the username/uid of the user who will own the target files
-g/--gid       -- the groupname/gid of the group who will own the target files
-r/--replace   -- specify replacement value for .in file

This script may be used to install a custom Zope instance home
skeleton directory.  It is most useful when used to install a skeleton
which does not follow the standard 'one-directory-as-instance-home'
paradigm used by the stock Zope source install.

The value of --targetdir should be the directory where you would like to copy
the skeleton hierarchy.  For many packagers, this will be "/" or "/usr"
or "/usr/local".

The value of --sourcedir should be a directory which contains a custom skeleton
hierarchy.   For many packagers, the skeleton source directory may contain
directories like "usr" and "bin" and these directories will contain files
and other directories, comprising an installation hierarchy suitable for your
platform.

The skeleton source hierarchy may contain any kind of file.  Files
in the skeleton hierarchy that end with a ".in" extension will go through
textual substitution before they are placed in the target directory.  When
they are placed in the target directory, the ".in" extension is removed.

Specify textual replacement values by passing one or more --replace= options
to the script.  The value of each replace option needs to be
in the following format: --replace=key:value.  'key' is the value that
will be replaced (minus the "<<" and ">>" values expected by the
replacement).  'value' is the value that should be used for replacement.

Files which do not have an ".in" extension are copied without substitution.
All file mode bits from files/dirs in the skeleton source directory are copied
along with the file/directory itself.  If the --uid and/or --gid flags are
used, all directories and files created by this script will be provided with
this owner and/or group.  Otherwise, the uid and group owner of the files will
be the executing user's.  Existing directory structures and files are left
unchanged.  If a file already exists in the target directory, it is left
unchanged and the source file is not copied.  If a directory already exists in
the target directory, its ownership information and mode bit settings are left
unchanged.
"""

import os
import shutil
import sys
import getopt

CVS_DIRS = [os.path.normcase("CVS"), os.path.normcase(".svn")]


def main():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hs:t:u:g:r:",
            ["help", "sourcedir=", "targetdir=", "uid=", "gid=",
             "replace="]
        )
    except getopt.GetoptError as msg:
        usage(sys.stderr, msg)
        sys.exit(2)

    sourcedir = None
    targetdir = None
    uid = None
    gid = None
    replacements = {}

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(sys.stdout)
            sys.exit()
        if opt in ("-s", "--sourcedir"):
            sourcedir = os.path.abspath(os.path.expanduser(arg))
            if not sourcedir:
                usage(sys.stderr, "sourcedir must not be empty")
                sys.exit(2)
        if opt in ("-t", "--targetdir"):
            targetdir = os.path.abspath(os.path.expanduser(arg))
            if not targetdir:
                usage(sys.stderr, "targetdir must not be empty")
                sys.exit(2)
        if opt in ("-u", "--uid"):
            if not arg:
                usage(sys.stderr, "uid must not be empty")
                sys.exit(2)
            try:
                if os.getuid() != 0:
                    usage(sys.stderr, "You must be root to specify a uid")
                    sys.exit(2)
                try:
                    uid = int(arg)
                except:
                    try:
                        import pwd
                        uid = pwd.getpwnam(arg)[2]
                        if not gid:
                            gid = pwd.getpwnam(arg)[3]
                    except KeyError:
                        usage(sys.stderr,
                              "The user indicated by uid does not exist on "
                              "your system")
                        sys.exit(2)
            except (ImportError, AttributeError):
                usage(sys.stderr,
                      "Your system does not support the gid or uid options")
                sys.exit(2)
        if opt in ("-g", "--gid"):
            if not arg:
                usage(sys.stderr, "gid must not be empty")
                sys.exit(2)
            try:
                if os.getuid() != 0:
                    usage(sys.stderr, "You must be root to specify a gid")
                    sys.exit(2)
                try:
                    gid = int(arg)
                except:
                    try:
                        import pwd
                        gid = pwd.getpwnam(arg)[3]
                    except KeyError:
                        usage(sys.stderr,
                              "The user indicated by gid does not exist on "
                              "your system")
                        sys.exit(2)
            except (ImportError, AttributeError):
                usage(sys.stderr,
                      "Your system does not support the gid or uid options")
                sys.exit(2)

        if opt in ("-r", "--replace"):
            if not arg:
                continue
            k, v = arg.split(':', 1)
            replacements[k] = v

    if not sourcedir:
        usage(sys.stderr, "Must specify sourcedir")
        sys.exit(2)

    if not targetdir:
        usage(sys.stderr, "Must specify targetdir")
        sys.exit(2)

    copyskel(sourcedir, targetdir, uid, gid, **replacements)


def copyskel(sourcedir, targetdir, uid, gid, **replacements):
    """ This is an independent function because we'd like to
    import and call it from mkzopeinstance """
    # Create the top of the instance:
    if not os.path.exists(targetdir):
        os.makedirs(targetdir)

    # This is fairly ugly.  The chdir() makes path manipulation in the
    # walk() callback a little easier (less magical), so we'll live
    # with it.
    pwd = os.getcwd()
    os.chdir(sourcedir)
    try:
        try:
            os.path.walk(os.curdir, copydir,
                         (targetdir, replacements, uid, gid))
        finally:
            os.chdir(pwd)
    except (IOError, OSError) as msg:
        print >>sys.stderr, msg
        sys.exit(1)


def copydir(args, sourcedir, names):
    targetdir, replacements, uid, gid = args
    # Don't recurse into CVS directories:
    for name in names[:]:
        if os.path.normcase(name) in CVS_DIRS:
            names.remove(name)
        elif os.path.isfile(os.path.join(sourcedir, name)):
            # Copy the file:
            sn, ext = os.path.splitext(name)
            if os.path.normcase(ext) == ".in":
                dst = os.path.join(targetdir, sourcedir, sn)
                if os.path.exists(dst):
                    continue
                copyin(os.path.join(sourcedir, name), dst, replacements, uid,
                       gid)
                if uid is not None:
                    os.chown(dst, uid, gid)
            else:
                src = os.path.join(sourcedir, name)
                dst = os.path.join(targetdir, src)
                if os.path.exists(dst):
                    continue
                shutil.copyfile(src, dst)
                shutil.copymode(src, dst)
                if uid is not None:
                    os.chown(dst, uid, gid)
        else:
            # Directory:
            dn = os.path.join(targetdir, sourcedir, name)
            if not os.path.exists(dn):
                os.mkdir(dn)
                shutil.copymode(os.path.join(sourcedir, name), dn)
                if uid is not None:
                    os.chown(dn, uid, gid)


def copyin(src, dst, replacements, uid, gid):
    ifp = open(src)
    text = ifp.read()
    ifp.close()
    for k in replacements:
        text = text.replace("<<%s>>" % k, replacements[k])
    ofp = open(dst, "w")
    ofp.write(text)
    ofp.close()
    shutil.copymode(src, dst)
    if uid is not None:
        os.chown(dst, uid, gid)


def usage(stream, msg=None):
    if msg:
        stream.write(msg)
        stream.write('\n')
    program = os.path.basename(sys.argv[0])
    stream.write(__doc__ % {"program": program})

if __name__ == '__main__':
    main()
