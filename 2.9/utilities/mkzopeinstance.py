#!/usr/bin/env python2.4

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

"""%(program)s:  Create a Zope instance home.

usage:  %(program)s [options]

Options:
-h/--help -- print this help text
-d/--dir  -- the dir in which the instance home should be created
-u/--user NAME:PASSWORD -- set the user name and password of the initial user
-s/--skelsrc -- the dir from which skeleton files should be copied

When run without arguments, this script will ask for the information necessary
to create a Zope instance home.
"""

import getopt
import os
import shutil
import sys
import copyzopeskel

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:],
            "hu:d:s:",
            ["help", "user=", "dir=", "skelsrc="]
            )
    except getopt.GetoptError, msg:
        usage(sys.stderr, msg)
        sys.exit(2)

    script = os.path.abspath(sys.argv[0])
    user = None
    password = None
    skeltarget = None
    skelsrc = None

    for opt, arg in opts:
        if opt in ("-d", "--dir"):
            skeltarget = os.path.abspath(os.path.expanduser(arg))
            if not skeltarget:
                usage(sys.stderr, "dir must not be empty")
                sys.exit(2)
        if opt in ("-s", "--skelsrc"):
            skelsrc = os.path.abspath(os.path.expanduser(arg))
            if not skelsrc:
                usage(sys.stderr, "skelsrc must not be empty")
                sys.exit(2)
        if opt in ("-h", "--help"):
            usage(sys.stdout)
            sys.exit()
        if opt in ("-u", "--user"):
            if not arg:
                usage(sys.stderr, "user must not be empty")
                sys.exit(2)
            if not ":" in arg:
                usage(sys.stderr, "user must be specified as name:password")
                sys.exit(2)
            user, password = arg.split(":", 1)

    if not skeltarget:
        # interactively ask for skeltarget and initial user name/passwd.
        # cant set custom instancehome in interactive mode, we default
        # to skeltarget.
        skeltarget = instancehome = os.path.abspath(
            os.path.expanduser(get_skeltarget())
            )

    instancehome = skeltarget
    zopehome = os.path.dirname(os.path.dirname(script))
    softwarehome = os.path.join(zopehome, "lib", "python")
    configfile = os.path.join(instancehome, 'etc', 'zope.conf')
    if skelsrc is None:
        # default to using stock Zope skeleton source
        skelsrc = os.path.join(zopehome, "skel")

    inituser = os.path.join(instancehome, "inituser")
    if not (user or os.path.exists(inituser)):
        user, password = get_inituser()

    # we need to distinguish between python.exe and pythonw.exe under
    # Windows.  Zope is always run using 'python.exe' (even for services),
    # however, it may be installed via pythonw.exe (as a sub-process of an
    # installer).  Thus, sys.executable may not be the executable we use.
    # We still provide both PYTHON and PYTHONW, but PYTHONW should never
    # need be used.
    psplit = os.path.split(sys.executable)
    exedir = os.path.join(*psplit[:-1])
    pythonexe = os.path.join(exedir, 'python.exe')
    pythonwexe = os.path.join(exedir, 'pythonw.exe')

    if ( os.path.isfile(pythonwexe) and os.path.isfile(pythonexe) and
         (sys.executable in [pythonwexe, pythonexe]) ):
        # we're using a Windows build with both python.exe and pythonw.exe
        # in the same directory
        PYTHON = pythonexe
        PYTHONW = pythonwexe
    else:
        # we're on UNIX or we have a nonstandard Windows setup
        PYTHON = PYTHONW = sys.executable

    kw = {
        "PYTHON":PYTHON,
        "PYTHONW":PYTHONW,
        "INSTANCE_HOME": instancehome,
        "SOFTWARE_HOME": softwarehome,
        "ZOPE_HOME": zopehome,
        }

    copyzopeskel.copyskel(skelsrc, skeltarget, None, None, **kw)
    if user and password:
        write_inituser(inituser, user, password)

def usage(stream, msg=None):
    if msg:
        print >>stream, msg
        print >>stream
    program = os.path.basename(sys.argv[0])
    print >>stream, __doc__ % {"program": program}

def get_skeltarget():
    print 'Please choose a directory in which you\'d like to install'
    print 'Zope "instance home" files such as database files, configuration'
    print 'files, etc.'
    print
    while 1:
        skeltarget = raw_input("Directory: ").strip()
        if skeltarget == '':
            print 'You must specify a directory'
            continue
        else:
            break
    return skeltarget

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

def write_inituser(fn, user, password):
    import binascii
    import sha
    fp = open(fn, "w")
    pw = binascii.b2a_base64(sha.new(password).digest())[:-1]
    fp.write('%s:{SHA}%s\n' % (user, pw))
    fp.close()
    os.chmod(fn, 0644)

if __name__ == "__main__":
    main()
