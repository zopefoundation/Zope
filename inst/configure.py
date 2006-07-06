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
Create a Makefile for building and installing Zope.
"""
import getopt
import os
import sys
import versions
import tempfile

QUIET=0

if sys.platform == 'win32':
    PREFIX = 'c:\\Zope-' + versions.ZOPE_MAJOR_VERSION
    IN_MAKEFILE = 'Makefile.win.in'
    MAKE_COMMAND='the Visual C++ batch file "VCVARS32.bat" and then "nmake"'
else:
    PREFIX = '/opt/Zope-' + versions.ZOPE_MAJOR_VERSION
    IN_MAKEFILE = 'Makefile.in'
    MAKE_COMMAND='make'

def main():
    # below assumes this script is in the BASE_DIR/inst directory
    global PREFIX
    BASE_DIR=os.path.abspath(os.path.dirname(os.path.dirname(sys.argv[0])))
    BUILD_BASE=os.path.join(os.getcwd(), 'build-base',
                            'python-%s.%s' % sys.version_info[:2])
    PYTHON=sys.executable
    TMP_DIR = tempfile.gettempdir()
    MAKEFILE=open(os.path.join(BASE_DIR, 'inst', IN_MAKEFILE)).read()
    REQUIRE_LF_ENABLED = 1
    REQUIRE_ZLIB = 1
    REQUIRE_EXPAT = 1 
    INSTALL_FLAGS = ''
    DISTUTILS_OPTS = ''
    try:
        longopts = ['help', 'ignore-largefile', 'ignore-zlib',
                    'ignore-expat', 'prefix=',
                    'build-base=', 'optimize', 'no-compile', 'quiet']
        opts, args = getopt.getopt(sys.argv[1:], 'h', longopts)
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
        if o == '--ignore-largefile':
            REQUIRE_LF_ENABLED=0
        if o == '--ignore-zlib':
            REQUIRE_ZLIB=0
        if o == '--ignore-expat':
            REQUIRE_EXPAT=0
        if o == '--optimize':
            INSTALL_FLAGS = '--optimize=1 --no-compile'
        if o == '--no-compile':
            INSTALL_FLAGS = '--no-compile'
        if o == '--build-base':
            BUILD_BASE = a
        if o == '--quiet':
            DISTUTILS_OPTS = '-q'
            global QUIET
            QUIET = 1
    if REQUIRE_LF_ENABLED:
        test_largefile()
    if REQUIRE_ZLIB:
        test_zlib()
    if REQUIRE_EXPAT:
        test_expat()
    out('  - Zope top-level binary directory will be %s.' % PREFIX)
    if INSTALL_FLAGS:
        out('  - Distutils install flags will be "%s"' % INSTALL_FLAGS)
    idata = {
        '<<PYTHON>>':PYTHON,
        '<<PREFIX>>':PREFIX,
        '<<BASE_DIR>>':BASE_DIR,
        '<<BUILD_BASE>>':BUILD_BASE,
        '<<TMP_DIR>>':TMP_DIR,
        '<<INSTALL_FLAGS>>':INSTALL_FLAGS,
        '<<ZOPE_MAJOR_VERSION>>':versions.ZOPE_MAJOR_VERSION,
        '<<ZOPE_MINOR_VERSION>>':versions.ZOPE_MINOR_VERSION,
        '<<VERSION_RELEASE_TAG>>':versions.VERSION_RELEASE_TAG,
        '<<DISTUTILS_OPTS>>':DISTUTILS_OPTS,
        }
    for k,v in idata.items():
        MAKEFILE = MAKEFILE.replace(k, v)
    f = open(os.path.join(os.getcwd(), 'makefile'), 'w')
    f.write(MAKEFILE)
    out('  - Makefile written.')
    out('')
    out('  Next, run %s.' % MAKE_COMMAND)
    out('')

def usage():
    usage = ("""
%(program)s configures and writes a Makefile for Zope.

Defaults for options are specified in brackets.

Configuration:

  -h, --help                    display this help and exit

Options:

  --quiet                       suppress nonessential output

  --ignore-zlib                 allow configuration to proceeed if
                                Python zlib module is not found.

  --ignore-largefile            allow configuration to proceed without
                                Python large file support.

  --ignore-expat                allow configuration to proceed if the expat
                                XML parsing module is not found.

  --optimize                    compile Python files as .pyo files
                                instead of as .pyc files

  --no-compile                  don't compile Python files

Directories:

  --build-base=DIR              use DIR to store temporary build files

  --prefix=DIR                  install Zope files in DIR [%(PREFIX)s]

By default, 'make install' will install Zope software files in
'%(PREFIX)s'  You can specify an alternate location for these
files by using '--prefix', for example: '--prefix=$HOME/zope'.
""" % ({'program':sys.argv[0], 'PREFIX':PREFIX})
             )
    print usage

def test_expat():
    try:
        import xml.parsers.expat
    except ImportError:
        print (
            """
The Python interpreter you are using does not appear to have the 'pyexpat'
library module installed.  For many Zope features to work properly, including
Zope Page Templates, you must install a Python interpreter which includes the
pyexpat module, or install the pyexpat library into your Python interpreter
manually.  The file which represents the library is named 'pyexpat.so' (UNIX)
or 'pyexpat.dll' (Windows) and is typically located in the 'lib-dynload'
directory of your Python's library directory.  Some Python packagers ship the
pyexpat module as a separate installable binary. If you are using a
system-provided Python installation, you may want to look for a 'python-xml'
or 'python-pyexpat' package (or something like it) and install it to make the
pyexpat module available to Zope.  If you've compiled your Python interpreter
from source, you may need to recompile and reinstall it after installing James
Clark's expat libraries and development packages (look for libexpat.so and
expat.h). Typically, these come as part of your operating system's libexpat
and libexpat-dev packages, respectively.

Run the configure script with the --ignore-expat option to prevent this
warning with the understanding that some Zope features may not work properly
until you've installed the pyexpat module.
"""
            )
        sys.exit(1)
        

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

def out(s):
    if not QUIET:
        print s
    
if __name__ == '__main__':
    main()
