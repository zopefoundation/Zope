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
-d/--dir -- the directory to which the instance files should be installed
-h/--help -- print this help text
-u/--user NAME:PASSWORD -- set the user name and password of the initial user
-z/--zeo host:port -- set the host:port of the ZEO server

If no arguments are specified, the installer will ask for dir, username, and
paassword.

"""

import getopt
import os
import shutil
import sys

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hu:z:d:", ["help", "user=",
            "zeo=", "dir="])
    except getopt.GetoptError, msg:
        usage(sys.stderr, msg)
        sys.exit(2)
    user = None
    password = None
    zeo = None
    dirname = None
    for opt, arg in opts:
        if opt in ("-d", "--dir"):
            dirname = os.path.abspath(arg)
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
        if opt in ("-z", "--zeo"):
            if not ":" in arg:
                usage(sys.stderr, "zeo server must be specified as host:port")
                sys.exit(2)
            zeo = tuple(arg.split(":", 1))
            try:
                int(zeo[1])
            except ValueError:
                usage(sys.stderr, "zeo server port must be a number")
                sys.exit(2)
    if not dirname:
        dirname = get_dirname()
    dirname = os.path.expanduser(dirname)
    inituser = os.path.join(dirname, "inituser")
    if not (user or os.path.exists(inituser)):
        user, password = get_inituser()
    makeinstance(dirname, user, password, inituser)
    if zeo:
        makezeo(dirname, zeo)

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

def makeinstance(dirname, user, password, inituser):
    script = os.path.abspath(sys.argv[0])
    installation = os.path.dirname(os.path.dirname(script))
    skel = os.path.join(installation, "skel")

    # Create the top of the instance:
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    replacements = {
        "PYTHON": sys.executable,
        "INSTANCE_HOME": dirname,
        "SOFTWARE_HOME": os.path.join(installation, "lib", "python"),
        "ZOPE_HOME": installation,
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

def makezeo(dirname, zeo):
    fp = open(os.path.join(dirname, 'custom_zodb.py'), 'w')
    print >>fp, "import ZEO.ClientStorage"
    print >>fp, "Storage=ZEO.ClientStorage.ClientStorage(('%s',%s))"%zeo
    fp.close()

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
