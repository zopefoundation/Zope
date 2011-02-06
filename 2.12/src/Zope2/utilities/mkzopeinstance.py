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

"""%(program)s:  Create a Zope instance home.

usage:  %(program)s [options]

Options:
-h/--help -- print this help text
-d/--dir  -- the dir in which the instance home should be created
-u/--user NAME:PASSWORD -- set the user name and password of the initial user
-s/--skelsrc -- the dir from which skeleton files should be copied
-p/--python -- the Python interpreter to use

When run without arguments, this script will ask for the information necessary
to create a Zope instance home.
"""

import getopt
import os
import sys
import copyzopeskel

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:],
            "hu:d:s:p:",
            ["help", "user=", "dir=", "skelsrc=", "python="]
            )
    except getopt.GetoptError, msg:
        usage(sys.stderr, msg)
        sys.exit(2)

    script_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    user = None
    password = None
    skeltarget = None
    skelsrc = None
    python = None

    if check_buildout(script_path):
        python = os.path.join(script_path, 'zopepy')

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
        if opt in ("-p", "--python"):
            python = os.path.abspath(os.path.expanduser(arg))
            if not os.path.exists(python) and os.path.isfile(python):
                usage(sys.stderr, "The Python interpreter does not exist.")
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
    configfile = os.path.join(instancehome, 'etc', 'zope.conf')
    if skelsrc is None:
        # default to using stock Zope skeleton source
        skelsrc = os.path.join(os.path.dirname(__file__), "skel")

    inituser = os.path.join(instancehome, "inituser")
    if not (user or os.path.exists(inituser)):
        user, password = get_inituser()

    # we need to distinguish between python.exe and pythonw.exe under
    # Windows.  Zope is always run using 'python.exe' (even for services),
    # however, it may be installed via pythonw.exe (as a sub-process of an
    # installer).  Thus, sys.executable may not be the executable we use.
    # We still provide both PYTHON and PYTHONW, but PYTHONW should never
    # need be used.
    if python is None:
        python = sys.executable
    
    psplit = os.path.split(python)
    exedir = os.path.join(*psplit[:-1])
    pythonexe = os.path.join(exedir, 'python.exe')
    pythonwexe = os.path.join(exedir, 'pythonw.exe')

    if ( os.path.isfile(pythonwexe) and os.path.isfile(pythonexe) and
         (python in [pythonwexe, pythonexe]) ):
        # we're using a Windows build with both python.exe and pythonw.exe
        # in the same directory
        PYTHON = pythonexe
        PYTHONW = pythonwexe
    else:
        # we're on UNIX or we have a nonstandard Windows setup
        PYTHON = PYTHONW = python

    zope2path = get_zope2path(PYTHON)

    kw = {
        "PYTHON":PYTHON,
        "PYTHONW":PYTHONW,
        "INSTANCE_HOME": instancehome,
        "ZOPE_SCRIPTS": script_path,
        "ZOPE2PATH": zope2path,
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
    try:
        from hashlib import sha1 as sha
    except:
        from sha import new as sha
    fp = open(fn, "w")
    pw = binascii.b2a_base64(sha(password).digest())[:-1]
    fp.write('%s:{SHA}%s\n' % (user, pw))
    fp.close()
    os.chmod(fn, 0644)

def check_buildout(script_path):
    """ Are we running from within a buildout which supplies 'zopepy'?
    """
    buildout_cfg = os.path.join(os.path.dirname(script_path), 'buildout.cfg')
    if os.path.exists(buildout_cfg):
        from ConfigParser import RawConfigParser
        parser = RawConfigParser()
        parser.read(buildout_cfg)
        return 'zopepy' in parser.sections()

def get_zope2path(python):
    """ Get Zope2 path from selected Python interpreter.
    """
    zope2file = ''
    p = os.popen('"%s" -c"import Zope2; print Zope2.__file__"' % python)
    try:
        zope2file = p.readline()[:-1]
    finally:
        p.close()
    if not zope2file:
        # fall back to current Python interpreter
        import Zope2
        zope2file = Zope2.__file__
    return os.path.abspath(os.path.dirname(os.path.dirname(zope2file)))

if __name__ == "__main__":
    main()
