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
"""
Create a Makefile for building and installing Zope.
"""
import getopt
import os
import sys

import versions

if sys.platform == 'win32':
    PREFIX = 'c:\\Zope-' + versions.ZOPE_MAJOR_VERSION
    IN_MAKEFILE = 'Makefile.win.in'
    MAKE_COMMAND='the Visual C++ batch file "VCVARS32.bat" and then "nmake build"'
else:
    PREFIX = '/opt/Zope-' + versions.ZOPE_MAJOR_VERSION
    IN_MAKEFILE = 'Makefile.in'
    MAKE_COMMAND='make'

def main():
    # below assumes this script is in the BASE_DIR/inst directory
    global PREFIX
    BASE_DIR=os.path.abspath(os.path.dirname(os.path.dirname(sys.argv[0])))
    BUILD_BASE=os.getcwd()
    PYTHON=sys.executable
    MAKEFILE=open(os.path.join(BASE_DIR, 'inst', IN_MAKEFILE)).read()
    REQUIRE_LF_ENABLED = 1
    REQUIRE_ZLIB=1
    INSTALL_FLAGS = ''
    DISTUTILS_OPTS = ''
    try:
        longopts = ["help", "ignore-largefile", "ignore-zlib", "prefix=",
                    "build-base=", "optimize", "quiet"]
        opts, args = getopt.getopt(sys.argv[1:], "h", longopts)
    except getopt.GetoptError, v:
        print v
        usage()
        sys.exit(1)
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
        if o == '--prefix':
            PREFIX=os.path.abspath(os.path.expanduser(a))
        if o == "--ignore-largefile":
            REQUIRE_LF_ENABLED=0
        if o == "--ignore-zlib":
            REQUIRE_ZLIB=0
        if o == "--optimize":
            INSTALL_FLAGS = '--optimize=1 --no-compile'
        if o == '--build-base':
            BUILD_BASE = a
        if o == '--quiet':
            DISTUTILS_OPTS = '-q'
    if REQUIRE_LF_ENABLED:
        test_largefile()
    if REQUIRE_ZLIB:
        test_zlib()
    print "  - Zope top-level binary directory will be %s." % PREFIX
    if INSTALL_FLAGS:
        print "  - Distutils install flags will be '%s'" % INSTALL_FLAGS
    idata = {
        '<<PYTHON>>':PYTHON,
        '<<PREFIX>>':PREFIX,
        '<<BASE_DIR>>':BASE_DIR,
        '<<BUILD_BASE>>':BUILD_BASE,
        '<<INSTALL_FLAGS>>':INSTALL_FLAGS,
        '<<ZOPE_MAJOR_VERSION>>':versions.ZOPE_MAJOR_VERSION,
        '<<ZOPE_MINOR_VERSION>>':versions.ZOPE_MINOR_VERSION,
        '<<VERSION_RELEASE_TAG>>':versions.VERSION_RELEASE_TAG,
        '<<DISTUTILS_OPTS>>':DISTUTILS_OPTS,
        }
    for k,v in idata.items():
        MAKEFILE = MAKEFILE.replace(k, v)
    f = open(os.path.join(BUILD_BASE, 'makefile'), 'w')
    f.write(MAKEFILE)
    print "  - Makefile written."
    print
    print "  Next, run %s." % MAKE_COMMAND
    print

def usage():
    usage = ("""
%(program)s configures and writes a Makefile for Zope.

Defaults for options are specified in brackets.

Configuration:

  -h, --help                    display this help and exit

Options:

  --ignore-zlib                 allow configuration to proceeed if
                                Python zlib module is not found.

  --ignore-largefile            allow configuration to proceed without
                                Python large file support.

  --optimize                    compile Python files as .pyo files
                                instead of as .pyc files

Directories:

  --build-base=DIR              use DIR to store temporary build files

  --prefix=DIR                  install Zope files in DIR [%(TARGET_DIR)s]

By default, 'make install' will install Zope software files in
'%(target_dir)s'  You can specify an alternate location for these
files by using '--prefix', for example: '--prefix=$HOME/zope'.
""" % ({'program':sys.argv[0], 'TARGET_DIR':TARGET_DIR})
             )
    print usage

def test_zlib():
    try:
        import zlib
    except ImportError:
        print (
            """
The Python interpreter you are using does not appear to have the 'zlib'
library module installed.  For Zope to be able to run, you must install a
Python interpreter which includes the zlib module, or install the zlib library
into your Python interpreter manually.  The file which represents the library
is named 'zlib.so' (UNIX) or 'zlib.dll' (Windows) and is typically located in
the 'lib-dynload' directory of your Python's library directory.  Some
Python packagers ship the zlib module as a separate installable binary. If you
are using a system-provided Python installation, you may want to look for
a 'python-zlib' package (or something like it) and install it to make the
Python zlib module available to Zope.

Run the configure script with the --ignore-zlib option to prevent this
warning with the understanding that Zope will not start properly until
you've installed the zlib module.
"""
            )
        sys.exit(1)
    except:
        print 'An error occurred while trying to import zlib!'
        import traceback; traceback.print_exc()
        sys.exit(1)

def test_largefile():
    OK=0
    f = open(sys.argv[0], 'r')
    try:
        # 2**31 == 2147483648
        f.seek(2147483649L)
        f.close()
        OK=1
    except (IOError, OverflowError):
        f.close()
    if OK:
        return
    print (
        """
This Python interpreter does not have 'large file support' enabled. Large
file support is required to allow the default Zope ZODB database to grow
larger than 2GB on most platforms.  Either install a Python interpreter with
large file support (see
http://www.python.org/doc/current/lib/posix-large-files.html) or run this
program again with the --ignore-largefile option to prevent this warning,
with the understanding that your Zope may fail if the ZODB database
size ever exceeds 2GB.
"""
        )
    sys.exit(1)

if __name__ == '__main__':
    main()
