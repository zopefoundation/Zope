#! python
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

"""%(program)s:  Create a Zope instance home.

usage:  %(program)s [options]

Options:
-d/--dir --  the directory to which the instance files should be installed
-h/--help -- print this help text
-u/--user NAME:PASSWORD -- set the user name and password of the initial user
-s/--skel -- the 'skeleton' directory which contains instance files
-z/--home -- the zope home directory (aka ZOPE_HOME) (defaults to ..)
-l/--lib --  the zope lib directory (aka SOFTWARE_HOME) (defaults to
             ../lib/python)

If no arguments are specified, the installer will ask for dir, username, and
password and will use ZOPEHOME/skel as the skeleton directory.
"""

import getopt
import os
import shutil
import sys

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:],
            "hu:z:d:s:z:l:",
            ["help", "user=", "dir=", "skel=", "home=", "lib="]
            )
    except getopt.GetoptError, msg:
        usage(sys.stderr, msg)
        sys.exit(2)

    script = os.path.abspath(sys.argv[0])
    user = None
    password = None
    dirname = None
    zopehome = None
    softwarehome = None
    skel = None

    for opt, arg in opts:
        if opt in ("-d", "--dir"):
            dirname = os.path.expanduser(os.path.abspath(arg))
            if not dirname:
                usage(sys.stderr, "dirname must not be empty")
                sys.exit(2)
        if opt in ("-h", "--help"):
            usage(sys.stdout)
            sys.exit()
        if opt in ("-u", "--user"):
            if not ":" in arg:
                usage(sys.stderr, "user must be specified as name:password")
                sys.exit(2)
            user, password = arg.split(":", 1)
        if opt in ("-s", "--skel"):
            skel = os.path.expanduser(os.path.abspath(arg))
            if not skel:
                usage(sys.stderr, "skel must not be empty")
                sys.exit(2)
        if opt in ("-h", "--home"):
            zopehome = os.path.expanduser(os.path.abspath(arg))
            if not zopehome:
                usage(sys.stderr, "home must not be empty")
                sys.exit(2)
        if opt in ("-l", "--lib"):
            softwarehome = os.path.expanduser(os.path.abspath(arg))
            if not softwarehome:
                usage(sys.stderr, "lib must not be empty")
                sys.exit(2)

    # interactively ask for dirname and initial user name/passwd
    if not dirname:
        dirname = get_dirname()
    dirname = os.path.expanduser(dirname)
    inituser = os.path.join(dirname, "inituser")
    if not (user or os.path.exists(inituser)):
        user, password = get_inituser()

    # use defaults for zopehome, softwarehome, and skel if they're not
    # given
    if zopehome is None:
        zopehome = os.path.dirname(os.path.dirname(script))
    if softwarehome is None:
        softwarehome = os.path.join(zopehome, "lib", "python")
    if skel is None:
        skel = os.path.join(zopehome, "skel")

    makeinstance(dirname, user, password, inituser, zopehome, softwarehome,
                 skel)

def usage(stream, msg=None):
    if msg:
        print >>stream, msg
        print >>stream
    program = os.path.basename(sys.argv[0])
    print >>stream, __doc__ % {"program": program}

def get_dirname():
    print 'Please choose a directory in which you\'d like to install'
    print 'Zope "instance home" files such as database files, configuration'
    print 'files, etc.'
    print
    while 1:
        dirname = raw_input("Directory: ").strip()
        if dirname == '':
            print 'You must specify a directory'
            continue
        else:
            break
    return dirname

def get_inituser():
    import getpass
    print 'Please choose a username and password for the initial user.'
    print 'These will be the credentials you use to initially manage'
    print 'your new Zope instance.'
    print
    user = raw_input("Username: ").strip()
    if user == '':
        return None, None
    while 1:
        passwd = getpass.getpass("Password: ")
        verify = getpass.getpass("Verify password: ")
        if verify == passwd:
            break
        else:
            passwd = verify = ''
            print "Password mismatch, please try again..."
    return user, passwd

def makeinstance(dirname, user, password, inituser, zopehome,
                 softwarehome, skel):
    # Create the top of the instance:
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    replacements = {
        "PYTHON": sys.executable,
        "INSTANCE_HOME": dirname,
        "SOFTWARE_HOME": softwarehome,
        "ZOPE_HOME": zopehome,
        }

    # This is fairly ugly.  The chdir() makes path manipulation in the
    # walk() callback a little easier (less magical), so we'll live
    # with it.
    pwd = os.getcwd()
    os.chdir(skel)
    try:
        try:
            os.path.walk(os.curdir, copyskel, (dirname, replacements))
        finally:
            os.chdir(pwd)
    except (IOError, OSError), msg:
        print >>sys.stderr, msg
        sys.exit(1)

    if user:
        write_inituser(inituser, user, password)

def write_inituser(fn, user, password):
    import binascii
    import sha
    fp = open(fn, "w")
    pw = binascii.b2a_base64(sha.new(password).digest())[:-1]
    fp.write('%s:{SHA}%s\n' % (user, pw))
    fp.close()
    os.chmod(fn, 0644)

CVS = os.path.normcase("CVS")

def copyskel((basedir, replacements), dirname, names):
    # Don't recurse into CVS directories:
    for name in names[:]:
        if os.path.normcase(name) == CVS:
            names.remove(name)
        elif os.path.isfile(os.path.join(dirname, name)):
            # Copy the file:
            sn, ext = os.path.splitext(name)
            if os.path.normcase(ext) == ".in":
                dst = os.path.join(basedir, dirname, sn)
                if os.path.exists(dst):
                    continue
                copyin(os.path.join(dirname, name), dst, replacements)
            else:
                src = os.path.join(dirname, name)
                dst = os.path.join(basedir, src)
                if os.path.exists(dst):
                    continue
                shutil.copyfile(src, dst)
        else:
            # Directory:
            dn = os.path.join(basedir, dirname, name)
            if not os.path.exists(dn):
                os.mkdir(dn)

def copyin(src, dst, replacements):
    ifp = open(src)
    text = ifp.read()
    ifp.close()
    for k in replacements:
        text = text.replace("<<%s>>" % k, replacements[k])
    ofp = open(dst, "w")
    ofp.write(text)
    ofp.close()
    shutil.copymode(src, dst)


if __name__ == "__main__":
    main()
