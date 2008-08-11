#!/usr/bin/env python2.4

##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
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
Distutils setup for Zope

  In-place building

    This builds extension modules in-place, much like build_extensions.py
    does.  Use 'setup.py' like this::

      python setup.py build_ext -i

  Installation

    This builds extension modules, compiles python modules, and installs
    everything needed to support Zope instances in the directory of
    your choosing.  For example, to use '/usr/local/lib/zope'::

      python setup.py install \
        --home=/usr/local/lib/zope \
        --install-platlib=/usr/local/lib/zope \
        --install-purelib=/usr/local/lib/zope
"""

import glob
import os
import sys
import shutil

import distutils.core

# Override install_data to install into module directories, and to support
# globbing on data_files.

from distutils.command.install import install
from distutils.command.install_data import install_data
from distutils.util import convert_path

where = os.path.split(__file__)[0]
sys.path.insert(0, os.path.join(where, 'inst'))
import versions
del sys.path[0]

ZOPE_VERSION = '%s%s-%s' % (versions.ZOPE_MAJOR_VERSION,  versions.ZOPE_MINOR_VERSION, versions.VERSION_RELEASE_TAG)

class ZopeInstallData(install_data):
    def finalize_options(self):
        self.set_undefined_options('install',
                                   ('install_purelib', 'install_dir'),
                                   ('root', 'root'),
                                   ('force', 'force'),
                                  )

    def run(self):
        self.mkpath(self.install_dir)
        for f in self.data_files:
            if isinstance(f, str):
                # it's a simple file, so copy it
                f = convert_path(f)
                gl = glob.glob(f)
                if len(gl) == 0:
                    raise distutils.core.DistutilsFileError, \
                          "can't copy '%s': no matching files" % f
                for g in gl:
                    if os.path.isfile(g):
                        if self.warn_dir:
                            self.warn("setup script did not provide a "
                                      "directory for '%s' -- installing "
                                      "right in '%s'" %
                                      (g, self.install_dir))
                        (out, _) = self.copy_file(g, self.install_dir)
                        self.outfiles.append(out)
            else:
                # it's a tuple with path to install to and a list of files
                dir = convert_path(f[0])
                if not os.path.isabs(dir):
                    dir = os.path.join(self.install_dir, dir)
                elif self.root:
                    dir = change_root(self.root, dir)
                self.mkpath(dir)
                for data in f[1]:
                    data = convert_path(data)
                    gl = glob.glob(data)
                    if len(gl) == 0:
                        raise distutils.core.DistutilsFileError, \
                              "can't copy '%s': no matching files" % data
                    for g in gl:
                        if os.path.isfile(g):
                            (out, _) = self.copy_file(g, dir)
                            self.outfiles.append(out)

# We create a custom "install scheme" that works the same way on all
# platforms.  We do this in order to prevent distutils from trying to
# guess where to put our files on a per-platform basis.

ZOPE_INSTALL_SCHEME = {
    'purelib': '$base/lib/python',
    'platlib': '$base/lib/python',
    'headers': '$base/lib/python',
    'scripts': '$base/bin',
    'data'   : '$base/lib/python',
    }

class ZopeInstall(install):
    # give distutils install step knowledge about build file placement options
    user_options = install.user_options + [
        ('build-base=', None, 'base directory for build library'),
        ('build-lib=', None, 'build directory for all distribution'),
        ('build-scripts=', None, 'build directory for scripts'),
        ('build-temp=', None, 'temporary build directory'),
        ]
    build_scripts = None
    build_temp = None

    def run(self):
        """ Override run to pass along build location info so
        we can use custom build directories """
        build = self.distribution.get_command_obj('build')
        build.build_base = self.build_base
        build.build_lib = self.build_lib
        build.build_scripts = self.build_scripts
        build.build_temp = self.build_temp

        install.run(self)

    def select_scheme(self, name):
        """
        Override the default platform installation schemes, ignoring whatever
        'name' is passed in.  For our purposes, we want to put all library,
        header, and data into [install_base]/lib/python.  Comment
        this method out to achieve distutils-standard platform-specific
        behavior for 'setup.py install'.  This is most useful if you set the
        [install-base] by using the '--prefix' or '--home' flags on the
        setup.py install command line.  Otherwise, all Zope software
        will probably be installed to your Python's 'lib/python' directory.
        """
        scheme = ZOPE_INSTALL_SCHEME
        import distutils.command.install
        for key in distutils.command.install.SCHEME_KEYS:
            attrname = 'install_' + key
            if getattr(self, attrname) is None:
                setattr(self, attrname, scheme[key])

class ZopeDistribution(distutils.core.Distribution):
    def __init__(self, attrs):
        distutils.core.Distribution.__init__(self, attrs)
        self.cmdclass["install"] = ZopeInstall
        self.cmdclass["install_data"] = ZopeInstallData

# presumes this script lives in the base dir
BASE_DIR=os.path.dirname(os.path.abspath(sys.argv[0]))

AUTHOR = 'Zope Corporation and Contributors'

# Most modules are in lib/python in the source distribution
PACKAGES_ROOT = os.path.join(BASE_DIR, 'lib', 'python')
os.chdir(PACKAGES_ROOT)


# Most of this is ripped from the Zope 3 setup.py.

from distutils import dir_util
from distutils.command.build import build as buildcmd
from distutils.command.build_ext import build_ext
from distutils.command.install_lib import install_lib as installcmd
from distutils.core import setup
from distutils.dist import Distribution
from distutils.extension import Extension


# This class serves multiple purposes.  It walks the file system looking for
# auxiliary files that distutils doesn't install properly, and it actually
# copies those files (when hooked into by distutils).  It also walks the file
# system looking for candidate packages for distutils to install as normal.
# The key here is that the package must have an __init__.py file.
class Finder:
    def __init__(self, ignore, prefix):
        self._files = []
        self._pkgs = {}
        self._ignore = ignore
        # We're finding packages in lib/python in the source dir, but we're
        # copying them directly under build/lib.<plat>.  So we need to lop off
        # the prefix when calculating the package names from the file names.
        self._plen = len(prefix) + 1

    def visit(self, dir, files):
        # First see if this is one of the packages we want to add, or if
        # we're really skipping this package.
        if '__init__.py' in files:
            aspkg = dir[self._plen:].replace(os.sep, '.')
            self._pkgs[aspkg] = True
            ignore = ('.py',) + self._ignore
        else:
            ignore = self._ignore
        # Add any extra files we're interested in
        for file in files:
            base, ext = os.path.splitext(file)
            if ext not in ignore:
                self._files.append(os.path.join(dir, file))

    def copy_files(self, cmd, outputbase):
        for file in self._files:
            dest = os.path.join(outputbase, file[self._plen:])
            # Make sure the destination directory exists
            dir = os.path.dirname(dest)
            if not os.path.exists(dir):
                dir_util.mkpath(dir)
            cmd.copy_file(file, dest)

    def get_packages(self):
        return self._pkgs.keys()

def remove_stale_bytecode(arg, dirname, names):
    names = map(os.path.normcase, names)
    for name in names:
        if name.endswith(".pyc") or name.endswith(".pyo"):
            srcname = name[:-1]
            if srcname not in names:
                fullname = os.path.join(dirname, name)
                print "Removing stale bytecode file", fullname
                os.unlink(fullname)
#
#   Aliases for directories containing headers, to allow for Zope3 extensions
#   to include headers via stuff like '#include "zope.proxy/proxy.h"
#
HEADER_PATH_ALIASES = {'zope.proxy': 'zope/proxy'}

# Create the finder instance, which will be used in lots of places.  `finder'
# is the global we're most interested in.
IGNORE_EXTS = ('.pyc', '.pyo', '.c', '.h', '.so', '.o', '.dll', '.lib', '.obj', '.cfg')
finder = Finder(IGNORE_EXTS, PACKAGES_ROOT)

for dirpath, dirnames, filenames in os.walk(PACKAGES_ROOT):
    if not '.svn' in dirpath:
        finder.visit(dirpath, filenames)
packages = finder.get_packages()

# Distutils hook classes
class MyBuilder(buildcmd):
    def run(self):
        os.path.walk(os.curdir, remove_stale_bytecode, None)
        buildcmd.run(self)
        finder.copy_files(self, self.build_lib)

class MyExtBuilder(build_ext):
    # Override the default build_ext to remove stale bytecodes.
    # Technically, removing bytecode has nothing to do with
    # building extensions, but Zope's the build_ext -i variant
    # is used to build Zope in place.
    #
    # Note that we also create make a copy for the oddball include
    # directories used by some Zope3 extensions.
    def run(self):
        os.path.walk(os.curdir, remove_stale_bytecode, None)
        for k, v in HEADER_PATH_ALIASES.items():
            if os.path.exists(k):
                shutil.rmtree(k)
            ignore = list(IGNORE_EXTS)
            ignore.remove('.h')
            f = Finder(tuple(ignore), v)
            for dirpath, dirnames, filenames in os.walk(v):
                if not '.svn' in dirpath:
                    f.visit(dirpath, filenames)
            f.copy_files(self, k)
        build_ext.run(self)

class MyLibInstaller(installcmd):
    def run(self):
        installcmd.run(self)
        finder.copy_files(self, self.install_dir)

class MyDistribution(Distribution):
    # To control the selection of MyLibInstaller and MyPyBuilder, we
    # have to set it into the cmdclass instance variable, set in
    # Distribution.__init__().
    def __init__(self, *attrs):
        Distribution.__init__(self, *attrs)
        self.cmdclass['install'] = ZopeInstall
        self.cmdclass['build'] = MyBuilder
        self.cmdclass['build_ext'] = MyExtBuilder
        self.cmdclass['install_lib'] = MyLibInstaller


EXTENSIONCLASS_INCLUDEDIRS = ['ExtensionClass', '.']

# All extension modules must be listed here.
ext_modules = [

    # AccessControl
    Extension(name='AccessControl.cAccessControl',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS+['Acquisition'],
              sources=['AccessControl/cAccessControl.c'],
              depends=['ExtensionClass/ExtensionClass.h',
                       'ExtensionClass/pickle/pickle.c',
                       'Acquisition/Acquisition.h']),


    # DocumentTemplate
    Extension(name='DocumentTemplate.cDocumentTemplate',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=['DocumentTemplate/cDocumentTemplate.c']),

    # ExtensionClass
    Extension(name='ExtensionClass._ExtensionClass',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=["ExtensionClass/_ExtensionClass.c"],
              depends=["ExtensionClass/ExtensionClass.h"]),
    Extension(name='Acquisition._Acquisition',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=["Acquisition/_Acquisition.c"],
              depends=["ExtensionClass/ExtensionClass.h",
                       "Acquisition/Acquisition.h"]),
    Extension(name='MethodObject._MethodObject',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=["MethodObject/_MethodObject.c"],
              depends=["ExtensionClass/ExtensionClass.h"]),
    Extension(name='MultiMapping._MultiMapping',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=["MultiMapping/_MultiMapping.c"],
              depends=["ExtensionClass/ExtensionClass.h"]),
    Extension(name='ThreadLock._ThreadLock',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=["ThreadLock/_ThreadLock.c"],
              depends=["ExtensionClass/ExtensionClass.h"]),
    Extension(name='Missing._Missing',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=["Missing/_Missing.c"],
              depends=["ExtensionClass/ExtensionClass.h"]),
    Extension(name='Record._Record',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=["Record/_Record.c"],
              depends=["ExtensionClass/ExtensionClass.h"]),
    Extension(name='ComputedAttribute._ComputedAttribute',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=["ComputedAttribute/_ComputedAttribute.c"],
              depends=["ExtensionClass/ExtensionClass.h"]),

    # initgroups
    Extension(name='initgroups._initgroups',
              sources=['initgroups/_initgroups.c']),

    # indexes
    Extension(name='Products.PluginIndexes.TextIndex.Splitter.ZopeSplitter.ZopeSplitter',
              sources=['Products/PluginIndexes/TextIndex/Splitter/ZopeSplitter/src/ZopeSplitter.c']),
    Extension(name='Products.PluginIndexes.TextIndex.Splitter.ISO_8859_1_Splitter.ISO_8859_1_Splitter',
              sources=['Products/PluginIndexes/TextIndex/Splitter/ISO_8859_1_Splitter/src/ISO_8859_1_Splitter.c']),
    Extension(name='Products.PluginIndexes.TextIndex.Splitter.UnicodeSplitter.UnicodeSplitter',
              sources=['Products/PluginIndexes/TextIndex/Splitter/UnicodeSplitter/src/UnicodeSplitter.c']),
    Extension(name='Products.ZCTextIndex.stopper',
              sources=['Products/ZCTextIndex/stopper.c']),
    Extension(name='Products.ZCTextIndex.okascore',
              sources=['Products/ZCTextIndex/okascore.c']),

    #ZODB
    Extension(name = 'persistent.cPersistence',
              include_dirs = ['persistent'],
              sources= ['persistent/cPersistence.c',
                        'persistent/ring.c'],
              depends = ['persistent/cPersistence.h',
                         'persistent/ring.h',
                         'persistent/ring.c']
              ),
    Extension(name = 'Persistence._Persistence',
              include_dirs = ['.', 'persistent', 'ExtensionClass'],
              sources = ['Persistence/_Persistence.c'],
              depends = ['persistent/cPersistence.h',
                         'ExtensionClass/ExtensionClass.h']
              ),
    Extension(name = 'persistent.cPickleCache',
              include_dirs = ['persistent'],
              sources= ['persistent/cPickleCache.c',
                        'persistent/ring.c'],
              depends = ['persistent/cPersistence.h',
                         'persistent/ring.h',
                         'persistent/ring.c']
              ),
    Extension(name = 'persistent.TimeStamp',
              sources= ['persistent/TimeStamp.c']
              ),

    #zope
    Extension("zope.proxy._zope_proxy_proxy",
              ["zope/proxy/_zope_proxy_proxy.c"],
              include_dirs = [".", "zope/proxy"],
              depends = ["zope/proxy/proxy.h"]),

    Extension("zope.security._proxy", ["zope/security/_proxy.c"],
              include_dirs = [".", "zope/proxy"],
              depends = ["zope/proxy/proxy.h"]),

    Extension("zope.security._zope_security_checker",
              ["zope/security/_zope_security_checker.c"],
              include_dirs = [],
              depends = []),

    Extension("zope.interface._zope_interface_coptimizations",
              ["zope/interface/_zope_interface_coptimizations.c"]),

    Extension("zope.i18nmessageid._zope_i18nmessageid_message",
              ["zope/i18nmessageid/_zope_i18nmessageid_message.c"]),

    Extension("zope.hookable._zope_hookable",
              ["zope/hookable/_zope_hookable.c"]),

    Extension("zope.app.container._zope_app_container_contained",
              ["zope/app/container/_zope_app_container_contained.c"],
              include_dirs = [".",
                              "persistent",
                              "zope/proxy",
                              "zope/app/container"],
              depends = [
                 "persistent/cPersistence.h",
                 "zope/proxy/_zope_proxy_proxy.c",
                 ]),

    ]

# BTree extension modules (code borrowed from ZODB/setup.py)

# Include directories for C extensions
include = ['.']

# Set up dependencies for the BTrees package
base_btrees_depends = [
    "BTrees/BTreeItemsTemplate.c",
    "BTrees/BTreeModuleTemplate.c",
    "BTrees/BTreeTemplate.c",
    "BTrees/BucketTemplate.c",
    "BTrees/MergeTemplate.c",
    "BTrees/SetOpTemplate.c",
    "BTrees/SetTemplate.c",
    "BTrees/TreeSetTemplate.c",
    "BTrees/sorters.c",
    "persistent/cPersistence.h",
    ]

_flavors = {"O": "object", "I": "int", "F": "float", 'L': 'int'}

KEY_H = "BTrees/%skeymacros.h"
VALUE_H = "BTrees/%svaluemacros.h"

def BTreeExtension(flavor):
    key = flavor[0]
    value = flavor[1]
    name = "BTrees._%sBTree" % flavor
    sources = ["BTrees/_%sBTree.c" % flavor]
    kwargs = {"include_dirs": include}
    if flavor != "fs":
        kwargs["depends"] = (base_btrees_depends + [KEY_H % _flavors[key],
                                                    VALUE_H % _flavors[value]])
    else:
        kwargs["depends"] = base_btrees_depends
    if key != "O":
        kwargs["define_macros"] = [('EXCLUDE_INTSET_SUPPORT', None)]
    return Extension(name, sources, **kwargs)

ext_modules += [BTreeExtension(flavor)
        for flavor in ("OO", "IO", "OI", "II", "IF",
                       "fs", "LO", "OL", "LL", "LF",
                       )]


# We're using the module docstring as the distutils descriptions.
doclines = __doc__.split("\n")

setup(name='Zope',
      author=AUTHOR,
      version="2.12.0-dev",
      maintainer="Zope Corporation",
      maintainer_email="zope-dev@zope.org",
      url = "http://www.zope.org/",
      ext_modules = ext_modules,
      license = "http://www.zope.org/Resources/ZPL",
      platforms = ["any"],
      description = doclines[0],
      long_description = "\n".join(doclines[2:]),
      packages = packages,
      distclass = MyDistribution,
      )

# The rest of these modules live in the root of the source tree
os.chdir(BASE_DIR)

IGNORE_NAMES = (
    'CVS', '.svn', # Revision Control Directories
    )

def skel_visit(skel, dirname, names):
    for ignore in IGNORE_NAMES:
        if ignore in names:
            names.remove(ignore)
    L = []
    for name in names:
        if os.path.isfile(os.path.join(dirname, name)):
            L.append("%s/%s" % (dirname, name))
    skel.append(("../../" + dirname, L))

installed_data_files = [
    ["../../doc", ['doc/*.txt']],
    ["../../bin", ['utilities/README.txt']],
    ]

os.path.walk("skel", skel_visit, installed_data_files)

setup(
    name='Zope',
    author=AUTHOR,

    data_files=installed_data_files,
    scripts=["utilities/mkzeoinstance.py",
             "utilities/mkzopeinstance.py",
             "utilities/check_catalog.py",
             "utilities/load_site.py",
             "utilities/requestprofiler.py",
             "utilities/zpasswd.py",
             "utilities/copyzopeskel.py",
             "utilities/reindex_catalog.py",
             "utilities/compilezpy.py",
             "utilities/decompilezpy.py",
             "utilities/ZODBTools/analyze.py",
             "utilities/ZODBTools/checkbtrees.py",
             "utilities/ZODBTools/fsdump.py",
             "utilities/ZODBTools/fsrefs.py" ,
             "utilities/ZODBTools/fstail.py",
             "utilities/ZODBTools/fstest.py",
             "utilities/ZODBTools/migrate.py",
             "utilities/ZODBTools/netspace.py",
             "utilities/ZODBTools/zodbload.py",
             "utilities/ZODBTools/repozo.py",
             "utilities/ZODBTools/space.py",
             "lib/python/ZEO/scripts/timeout.py",
             "lib/python/ZEO/scripts/parsezeolog.py",
             "lib/python/ZEO/scripts/zeopack.py",
             "lib/python/ZEO/scripts/zeoqueue.py",
             "lib/python/ZEO/scripts/zeoreplay.py",
             "lib/python/ZEO/scripts/zeoserverlog.py",
             "lib/python/ZEO/scripts/zeoup.py",
             "test.py"],
    distclass=ZopeDistribution,
    )
