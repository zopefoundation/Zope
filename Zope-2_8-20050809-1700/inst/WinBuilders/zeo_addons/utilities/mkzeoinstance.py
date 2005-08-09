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

"""%(program)s:  Create a ZEO instance home.

usage:  %(program)s [options]

Options:
-h/--help -- print this help text
-d/--dir  -- the dir in which the instance home should be created
-u/--user NAME:PASSWORD -- set the user name and password of the initial user
-s/--skelsrc -- the dir from which skeleton files should be copied

When run without arguments, this script will ask for the information necessary
to create a ZEO instance home.
"""

import getopt
import os
import shutil
import sys
import copyskel

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

    if not skeltarget:
        # interactively ask for skeltarget and initial user name/passwd.
        # cant set custom instancehome in interactive mode, we default
        # to skeltarget.
        skeltarget = instancehome = os.path.abspath(
            os.path.expanduser(get_skeltarget())
            )

    instancehome = skeltarget
    zeohome = os.path.dirname(os.path.dirname(script))
    softwarehome = os.path.join(zeohome, "lib", "python")
    if skelsrc is None:
        # default to using stock ZEO skeleton source
        skelsrc = os.path.join(zeohome, "skel")

    inituser = os.path.join(instancehome, "inituser")

    kw = {
        "PYTHON": sys.executable,
        "INSTANCE_HOME": instancehome,
        "SOFTWARE_HOME": softwarehome,
        "ZEO_HOME": zeohome,
        }
    copyskel.copyskel(skelsrc, skeltarget, None, None, **kw)

def usage(stream, msg=None):
    if msg:
        print >>stream, msg
        print >>stream
    program = os.path.basename(sys.argv[0])
    print >>stream, __doc__ % {"program": program}

def get_skeltarget():
    print 'Please choose a directory in which you\'d like to install'
    print 'ZEO "instance home" files such as database files, configuration'
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

if __name__ == "__main__":
    main()
