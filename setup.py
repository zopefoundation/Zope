#! /usr/bin/env python
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
        --home=/usr/local/lib/zope
        --install-platlib=/usr/local/lib/zope
        --install-purelib=/usr/local/lib/zope

    Note that with this method, all packages and scripts (including
    ZServer and z2.py) go in the same directory as Zope modules, which
    are distributed in lib/python.  You will need to set both ZOPE_HOME
    and SOFTWARE_HOME to point to your destination directory in order
    for Zope to work in this configuration.
"""

import os
import sys

from distutils.core import setup as distutils_setup
from distutils.extension import Extension

# This function collects setup information for one massive distutils
# run to be done at the end of the script.  If you're making a setup.py
# to use modules from Zope separately, you should be able to cut-and-paste
# the individual setup calls out into your own setup.py and it should
# Just Work(tm).

setup_info = {}
def setup(name=None, author=None, cmdclass=None, **kwargs):
    setup_info = sys.modules[__name__].setup_info
    for keyword in kwargs.keys():
	if not setup_info.has_key(keyword):
	    setup_info[keyword] = []	
	setup_info[keyword] += kwargs[keyword]

# Override install_data to install into module directories, and to support
# globbing on data_files.

from types import StringType
from distutils.command.install_data import install_data
from distutils.errors import DistutilsFileError
from distutils.util import convert_path
from glob import glob

class install_data(install_data):
    def finalize_options(self):
        self.set_undefined_options('install',
                                   ('install_purelib', 'install_dir'),
                                   ('root', 'root'),
                                   ('force', 'force'),
                                  )

    def run(self):
        self.mkpath(self.install_dir)
        for f in self.data_files:
            if type(f) == StringType:
                # it's a simple file, so copy it
                f = convert_path(f)
                gl = glob(f)
                if len(gl) == 0:
                    raise DistutilsFileError, \
                          "can't copy '%s': glob failed" % f
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
                    gl = glob(data)
                    if len(gl) == 0:
                        raise DistutilsFileError, \
                              "can't copy '%s': glob failed" % data
                    for g in gl:
                        if os.path.isfile(g):
                            (out, _) = self.copy_file(g, dir)
                            self.outfiles.append(out)

AUTHOR = 'Zope Corporation and Contributors'
ZOPE_ROOT = os.path.abspath(os.getcwd())
EXTENSIONCLASS_ROOT = os.path.join(ZOPE_ROOT, 'lib', 'Components', 'ExtensionClass')
EXTENSIONCLASS_SRCDIR = os.path.join(EXTENSIONCLASS_ROOT, 'src')
PACKAGES_ROOT = os.path.join(ZOPE_ROOT, 'lib', 'python')
EXTENSIONCLASS_INCLUDEDIRS = [EXTENSIONCLASS_SRCDIR]

# Most modules are in lib/python in the source distribution
os.chdir(PACKAGES_ROOT)

# AccessControl
setup(
    name='AccessControl',
    author=AUTHOR,

    packages=['AccessControl', 'AccessControl.securitySuite',
              'AccessControl.tests', 'AccessControl.tests.mixed_module',
              'AccessControl.tests.mixed_module.submodule',
              'AccessControl.tests.private_module',
              'AccessControl.tests.private_module.submodule',
              'AccessControl.tests.public_module',
              'AccessControl.tests.public_module.submodule'],

    data_files=[['AccessControl', ['AccessControl/*.txt']],
                ['AccessControl/dtml', ['AccessControl/dtml/*']],
                ['AccessControl/securitySuite',
                    ['AccessControl/securitySuite/README']],
                ['AccessControl/www', ['AccessControl/www/*']]],
    cmdclass={'install_data': install_data},

    ext_modules=[
        Extension(name='AccessControl.cAccessControl',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['AccessControl/cAccessControl.c'])]
)

# App
setup(
    name='App',
    author=AUTHOR,

    packages=['App'],

    data_files=[['App/dtml', ['App/dtml/*']],
                ['App/www', ['App/www/*']]],
    cmdclass={'install_data': install_data}
)

# BTrees
setup(
    name='BTrees',
    author=AUTHOR,

    packages=['BTrees', 'BTrees.tests'],

    ext_modules=[
        Extension(name='BTrees._OOBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['ZODB'],
                  sources=['BTrees/_OOBTree.c']),
        Extension(name='BTrees._OIBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['ZODB'],
                  sources=['BTrees/_OIBTree.c']),
        Extension(name='BTrees._IIBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['ZODB'],
                  define_macros=[('EXCLUDE_INTSET_SUPPORT', None)],
                  sources=['BTrees/_IIBTree.c']),
        Extension(name='BTrees._IOBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['ZODB'],
                  define_macros=[('EXCLUDE_INTSET_SUPPORT', None)],
                  sources=['BTrees/_IOBTree.c']),
        Extension(name='BTrees._fsBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['ZODB'],
                  define_macros=[('EXCLUDE_INTSET_SUPPORT', None)],
                  sources=['BTrees/_fsBTree.c'])],

    data_files=[['BTrees', ['BTrees/Maintainer.txt']]],
    cmdclass={'install_data': install_data}
)

# BTrees compatibility package
setup(
    name='BTree',
    author=AUTHOR,

    #headers=['../Components/BTree/intSet.h'],
    ext_modules=[
        Extension(name='BTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['ZODB'],
                  sources=['../Components/BTree/BTree.c']),
        Extension(name='IIBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['ZODB'],
                  sources=['../Components/BTree/IIBTree.c']),
        Extension(name='IOBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['ZODB'],
                  sources=['../Components/BTree/IOBTree.c']),
        Extension(name='OIBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['ZODB'],
                  sources=['../Components/BTree/OIBTree.c']),
        Extension(name='intSet',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['ZODB'],
                  sources=['../Components/BTree/intSet.c'])]
)

# DateTime
setup(
    name='DateTime',
    author=AUTHOR,

    packages=['DateTime', 'DateTime.tests'],

    data_files=[['DateTime', ['DateTime/DateTime.html']],
                ['DateTime/tests', ['DateTime/tests/julian_testdata.txt.gz']]],
    cmdclass={'install_data': install_data}
)

# DocumentTemplate
setup(
    name='DocumentTemplate',
    author=AUTHOR,

    packages=['DocumentTemplate', 'DocumentTemplate.sequence',
              'DocumentTemplate.sequence.tests', 'DocumentTemplate.tests'],

    data_files=[['DocumentTemplate', ['DocumentTemplate/Let.stx']],
                ['DocumentTemplate/tests',
                    ['DocumentTemplate/tests/dealers.*']]],
    cmdclass={'install_data': install_data},

    ext_modules=[
        Extension(name='DocumentTemplate.cDocumentTemplate',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['DocumentTemplate/cDocumentTemplate.c'])]
)

# ExtensionClass
setup(
    name='ExtensionClass',
    author=AUTHOR,

    ext_modules=[
        Extension(name='ExtensionClass',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['../Components/ExtensionClass/src/ExtensionClass.c']),
        Extension(name='Acquisition',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['../Components/ExtensionClass/src/Acquisition.c']),
        Extension(name='MethodObject',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['../Components/ExtensionClass/src/MethodObject.c']),
        Extension(name='MultiMapping',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['../Components/ExtensionClass/src/MultiMapping.c']),
        Extension(name='ThreadLock',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['../Components/ExtensionClass/src/ThreadLock.c']),
        Extension(name='Missing',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['../Components/ExtensionClass/src/Missing.c']),
        Extension(name='Sync',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['../Components/ExtensionClass/src/Sync.c']),
        Extension(name='Record',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['../Components/ExtensionClass/src/Record.c']),
        Extension(name='ComputedAttribute',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['../Components/ExtensionClass/src/ComputedAttribute.c'])]
)

# HelpSys
setup(
    name='HelpSys',
    author=AUTHOR,

    packages=['HelpSys'],

    data_files=[['HelpSys/dtml', ['HelpSys/dtml/*']],
                ['HelpSys/images', ['HelpSys/images/*']]],
    cmdclass={'install_data': install_data}
)

# Interface
setup(
    name='Interface',
    author=AUTHOR,

    packages=['Interface', 'Interface.tests',
              'Interface.Common', 'Interface.Common.tests'],

    cmdclass={'install_data': install_data}
)

# OFS
setup(
    name='OFS',
    author=AUTHOR,

    packages=['OFS', 'OFS.tests'],

    data_files=[['OFS/dtml', ['OFS/dtml/*']],
                ['OFS/standard', ['OFS/standard/*']],
                ['OFS/www', ['OFS/www/*']]],
    cmdclass={'install_data': install_data}
)

# RestrictedPython
setup(
    name='RestrictedPython',
    author=AUTHOR,

    packages=['RestrictedPython', 'RestrictedPython.compiler_2_1',
              'RestrictedPython.tests'],

    data_files=[['RestrictedPython/compiler_2_1',
                    ['RestrictedPython/compiler_2_1/ast.txt']]],
    cmdclass={'install_data': install_data}
)

# SearchIndex
setup(
    name='SearchIndex',
    author=AUTHOR,

    packages=['SearchIndex', 'SearchIndex.tests'],

    data_files=[['SearchIndex', ['SearchIndex/*.txt']]],
    cmdclass={'install_data': install_data},

    ext_modules=[
        Extension(name='SearchIndex.Splitter',
                  sources=['SearchIndex/Splitter.c'])]
)

# Shared.DC bases
setup(
    name='Shared.DC',
    author=AUTHOR,

    packages=['Shared', 'Shared.DC']
)

# Scripts
setup(
    name='Scripts',
    author=AUTHOR,

    packages=['Shared.DC.Scripts'],

    data_files=[['Shared/DC/Scripts/dtml', ['Shared/DC/Scripts/dtml/*']]],
    cmdclass={'install_data': install_data}
)

# StructuredText
setup(
    name='StructuredText',
    author=AUTHOR,

    packages=['StructuredText', 'StructuredText.regressions',
              'StructuredText.tests'],

    data_files=[['StructuredText', ['StructuredText/*.txt']],
                ['StructuredText/regressions',
                    ['StructuredText/regressions/*.ref',
                     'StructuredText/regressions/*.stx']]],
    cmdclass={'install_data': install_data}
)

# ZRDB
setup(
    name='ZRDB',
    author=AUTHOR,

    packages=['Shared.DC.ZRDB'],

    data_files=[['Shared/DC/ZRDB/dtml', ['Shared/DC/ZRDB/dtml/*']],
                ['Shared/DC/ZRDB/www', ['Shared/DC/ZRDB/www/*']]],
    cmdclass={'install_data': install_data}
)

# dcpyexpat
PYEXPAT_DIR=os.path.join(PACKAGES_ROOT, 'Shared', 'DC', 'xml', 'pyexpat')
DCPYEXPAT_INCLUDEDIRS=[os.path.join(PYEXPAT_DIR, 'expat', 'xmlparse'),
                       os.path.join(PYEXPAT_DIR, 'expat', 'xmltok')]

setup(
    name='dcpyexpat',
    author=AUTHOR,

    packages=['Shared.DC.xml', 'Shared.DC.xml.pyexpat'],

    data_files=[['Shared/DC/xml/pyexpat', ['Shared/DC/xml/pyexpat/README']]],
    cmdclass={'install_data': install_data},

    ext_modules=[
        Extension(name='Shared.DC.xml.pyexpat.dcpyexpat',
                  include_dirs=DCPYEXPAT_INCLUDEDIRS,
                  define_macros=[('XML_NS', None)],
                  sources=[PYEXPAT_DIR + '/expat/xmlparse/xmlparse.c',
                           PYEXPAT_DIR + '/expat/xmlparse/hashtable.c',
                           PYEXPAT_DIR + '/expat/xmltok/xmlrole.c',
                           PYEXPAT_DIR + '/expat/xmltok/xmltok.c',
                           PYEXPAT_DIR + '/dcpyexpat.c'])]
)

# TAL
setup(
    name='TAL',
    author=AUTHOR,

    packages=['TAL', 'TAL.tests'],

    data_files=[['TAL', ['TAL/*.txt']],
                ['TAL/benchmark', ['TAL/benchmark/*']],
                ['TAL/tests/input', ['TAL/tests/input/*']],
                ['TAL/tests/output', ['TAL/tests/output/*']]],
    cmdclass={'install_data': install_data}
)

# Testing
setup(
    name='Testing',
    author=AUTHOR,

    packages=['Testing'],

    data_files=[['Testing', ['Testing/README.txt']],
                ['Testing/var', ['Testing/var/README.txt']]],
    cmdclass={'install_data': install_data}
)

# ThreadedAsync
setup(
    name='ThreadedAsync',
    author=AUTHOR,

    packages=['ThreadedAsync']
)

# TreeDisplay
setup(
    name='TreeDisplay',
    author=AUTHOR,

    packages=['TreeDisplay'],

    data_files=[['TreeDisplay/www', ['TreeDisplay/www/*']]],
    cmdclass={'install_data': install_data}
)

# ZClasses
setup(
    name='ZClasses',
    author=AUTHOR,

    packages=['ZClasses'],

    data_files=[['ZClasses', ['ZClasses/*.gif']],
                ['ZClasses/dtml', ['ZClasses/dtml/*']]],
    cmdclass={'install_data': install_data}
)

# ZLogger
setup(
    name='ZLogger',
    author=AUTHOR,

    packages=['ZLogger']
)

# ZODB
setup(
    name='ZODB',
    author=AUTHOR,

    packages=['Persistence', 'ZODB', 'ZODB.tests'],

    ext_modules=[
        Extension(name='ZODB.cPersistence',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['ZODB/cPersistence.c']),
        Extension(name='ZODB.cPickleCache',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['ZODB/cPickleCache.c']),
        Extension(name='ZODB.TimeStamp',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  define_macros=[('USE_EXTENSION_CLASS', 1)],
                  sources=['ZODB/TimeStamp.c']),
        Extension(name='ZODB.coptimizations',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['ZODB/coptimizations.c']),
        Extension(name='ZODB.winlock',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['ZODB/winlock.c'])],
)

# ZPublisher
setup(
    name='ZPublisher',
    author=AUTHOR,

    packages=['ZPublisher', 'ZPublisher.tests'],
    cmdclass={'install_data': install_data}
)

# ZTUtils
setup(
    name='ZTUtils',
    author=AUTHOR,

    packages=['ZTUtils', 'ZTUtils.tests'],

    data_files=[['ZTUtils', ['ZTUtils/*.txt']]],
    cmdclass={'install_data': install_data}
)

# Zope
setup(
    name='Zope',
    author=AUTHOR,

    packages=['Zope']
)

# webdav
setup(
    name='webdav',
    author=AUTHOR,

    packages=['webdav'],

    data_files=[['webdav/dtml', ['webdav/dtml/*']],
                ['webdav/www', ['webdav/www/*']]],
    cmdclass={'install_data': install_data}
)

# zExceptions
setup(
    name='zExceptions',
    author=AUTHOR,

    packages=['zExceptions', 'zExceptions.tests']
)

# zLOG
setup(
    name='zLOG',
    author=AUTHOR,

    packages=['zLOG', 'zLOG.tests']
)

# zdaemon
setup(
    name='zdaemon',
    author=AUTHOR,

    packages=['zdaemon', 'zdaemon.tests']
)

# zlib
setup(
    name='zlib',
    author=AUTHOR,

    ext_modules=[
        Extension(name='zlib',
                  include_dirs=['../Components/zlib'],
                  sources=['../Components/zlib/adler32.c',
                           '../Components/zlib/compress.c',
                           '../Components/zlib/crc32.c',
                           '../Components/zlib/gzio.c',
                           '../Components/zlib/uncompr.c',
                           '../Components/zlib/deflate.c',
                           '../Components/zlib/trees.c',
                           '../Components/zlib/zutil.c',
                           '../Components/zlib/inflate.c',
                           '../Components/zlib/infblock.c',
                           '../Components/zlib/inftrees.c',
                           '../Components/zlib/infcodes.c',
                           '../Components/zlib/infutil.c',
                           '../Components/zlib/inffast.c',
                           '../Components/zlib/zlib.c'])]
)

# initgroups
setup(
    name='initgroups',
    author=AUTHOR,

    ext_modules=[
        Extension(name='initgroups',
                  sources=['../Components/initgroups/initgroups.c'])]
)

# Other top-level packages (XXX should these be broken out at all?)
setup(
    name='Top-level',
    author=AUTHOR,

    py_modules=['Globals', 'ImageFile', 'LOG', 'Main', 'dcdb', 'tempfile',
                'ts_regex', 'xmlrpclib', 'SignalHandler']
)

# Products base directory
setup(
    name='Products',
    author=AUTHOR,

    packages=['Products']
)

# ExternalMethod product
setup(
    name='ExternalMethod',
    author=AUTHOR,

    packages=['Products.ExternalMethod', 'Products.ExternalMethod.tests',
              'Products.ExternalMethod.tests.Extensions'],

    data_files=[['Products/ExternalMethod',
                    ['Products/ExternalMethod/*.gif',
                     'Products/ExternalMethod/*.txt']],
                ['Products/ExternalMethod/dtml',
                    ['Products/ExternalMethod/dtml/*']],
                ['Products/ExternalMethod/help',
                    ['Products/ExternalMethod/help/*']],
                ['Products/ExternalMethod/www',
                    ['Products/ExternalMethod/www/*']]],
    cmdclass={'install_data': install_data}
)

# MIMETools product
setup(
    name='MIMETools',
    author=AUTHOR,

    packages=['Products.MIMETools'],

    data_files=[['Products/MIMETools', ['Products/MIMETools/*.txt']]],
    cmdclass={'install_data': install_data}
)

# MailHost product
setup(
    name='MailHost',
    author=AUTHOR,

    packages=['Products.MailHost', 'Products.MailHost.help',
              'Products.MailHost.tests'],

    data_files=[['Products/MailHost', ['Products/MailHost/*.txt']],
                ['Products/MailHost/dtml', ['Products/MailHost/dtml/*']],
                ['Products/MailHost/help', ['Products/MailHost/help/*.stx']],
                ['Products/MailHost/www', ['Products/MailHost/www/*']]],
    cmdclass={'install_data': install_data}
)

# OFSP product
setup(
    name='OFSP',
    author=AUTHOR,

    packages=['Products.OFSP', 'Products.OFSP.help'],

    data_files=[['Products/OFSP', ['Products/OFSP/*.txt']],
                ['Products/OFSP/dtml', ['Products/OFSP/dtml/*']],
                ['Products/OFSP/help', ['Products/OFSP/help/*.stx']],
                ['Products/OFSP/images', ['Products/OFSP/images/*']]],
    cmdclass={'install_data': install_data}
)

# PageTemplates product
setup(
    name='PageTemplates',
    author=AUTHOR,

    packages=['Products.PageTemplates', 'Products.PageTemplates.help',
              'Products.PageTemplates.tests'],

    data_files=[['Products/PageTemplates', ['Products/PageTemplates/*.txt']],
                ['Products/PageTemplates/examples',
                    ['Products/PageTemplates/examples/*']],
                ['Products/PageTemplates/help',
                    ['Products/PageTemplates/help/*.stx']],
                ['Products/PageTemplates/tests/input',
                    ['Products/PageTemplates/tests/input/*']],
                ['Products/PageTemplates/tests/output',
                    ['Products/PageTemplates/tests/output/*']],
                ['Products/PageTemplates/www',
                    ['Products/PageTemplates/www/*']]],
    cmdclass={'install_data': install_data}
)

# PluginIndexes product
setup(
    name='PluginIndexes',
    author=AUTHOR,

    packages=['Products.PluginIndexes',
	      'Products.PluginIndexes.DateIndex',
	      'Products.PluginIndexes.DateIndex.tests',
	      'Products.PluginIndexes.DateRangeIndex',
	      'Products.PluginIndexes.DateRangeIndex.tests',
	      'Products.PluginIndexes.FieldIndex',
              'Products.PluginIndexes.FieldIndex.tests',
              'Products.PluginIndexes.KeywordIndex',
              'Products.PluginIndexes.KeywordIndex.tests',
              'Products.PluginIndexes.PathIndex',
              'Products.PluginIndexes.PathIndex.tests',
              'Products.PluginIndexes.TextIndex',
              'Products.PluginIndexes.TextIndex.Splitter',
              'Products.PluginIndexes.TextIndex.Splitter.ISO_8859_1_Splitter',
              'Products.PluginIndexes.TextIndex.Splitter.UnicodeSplitter',
              'Products.PluginIndexes.TextIndex.Splitter.UnicodeSplitter.tests',
              'Products.PluginIndexes.TextIndex.Splitter.ZopeSplitter',
              'Products.PluginIndexes.TextIndex.tests',
              'Products.PluginIndexes.TopicIndex',
              'Products.PluginIndexes.TopicIndex.tests',
              'Products.PluginIndexes.common'],

    data_files=[['Products/PluginIndexes', ['Products/PluginIndexes/*.txt']],
                ['Products/PluginIndexes/DateIndex',
		    ['Products/PluginIndexes/DateIndex/README.txt']],
                ['Products/PluginIndexes/DateIndex/dtml',
                    ['Products/PluginIndexes/DateIndex/dtml/*']],
                ['Products/PluginIndexes/DateRangeIndex',
		    ['Products/PluginIndexes/DateRangeIndex/README.txt']],
                ['Products/PluginIndexes/DateRangeIndex/dtml',
                    ['Products/PluginIndexes/DateRangeIndex/dtml/*']],
                ['Products/PluginIndexes/FieldIndex/dtml',
                    ['Products/PluginIndexes/FieldIndex/dtml/*']],
                ['Products/PluginIndexes/FieldIndex/help',
                    ['Products/PluginIndexes/FieldIndex/help/*']],
                ['Products/PluginIndexes/KeywordIndex/dtml',
                    ['Products/PluginIndexes/KeywordIndex/dtml/*']],
                ['Products/PluginIndexes/KeywordIndex/help',
                    ['Products/PluginIndexes/KeywordIndex/help/*']],
                ['Products/PluginIndexes/PathIndex',
                    ['Products/PluginIndexes/PathIndex/*.txt']],
                ['Products/PluginIndexes/PathIndex/dtml',
                    ['Products/PluginIndexes/PathIndex/dtml/*']],
                ['Products/PluginIndexes/PathIndex/help',
                    ['Products/PluginIndexes/PathIndex/help/*']],
                ['Products/PluginIndexes/TextIndex/dtml',
                    ['Products/PluginIndexes/TextIndex/dtml/*']],
                ['Products/PluginIndexes/TextIndex/help',
                    ['Products/PluginIndexes/TextIndex/help/*']],
                ['Products/PluginIndexes/TopicIndex',
                    ['Products/PluginIndexes/TopicIndex/*.txt']],
                ['Products/PluginIndexes/TopicIndex/dtml',
                    ['Products/PluginIndexes/TopicIndex/dtml/*']],
                ['Products/PluginIndexes/TopicIndex/help',
                    ['Products/PluginIndexes/TopicIndex/help/*']],
                ['Products/PluginIndexes/help',
                    ['Products/PluginIndexes/help/*']],
                ['Products/PluginIndexes/www',
                    ['Products/PluginIndexes/www/*']]],
    cmdclass={'install_data': install_data},

    ext_modules=[
        Extension(name='Products.PluginIndexes.TextIndex.Splitter.ZopeSplitter.ZopeSplitter',
                  sources=['Products/PluginIndexes/TextIndex/Splitter/ZopeSplitter/src/ZopeSplitter.c']),
        Extension(name='Products.PluginIndexes.TextIndex.Splitter.ISO_8859_1_Splitter.ISO_8859_1_Splitter',
                  sources=['Products/PluginIndexes/TextIndex/Splitter/ISO_8859_1_Splitter/src/ISO_8859_1_Splitter.c']),
        Extension(name='Products.PluginIndexes.TextIndex.Splitter.UnicodeSplitter.UnicodeSplitter',
                  sources=['Products/PluginIndexes/TextIndex/Splitter/UnicodeSplitter/src/UnicodeSplitter.c'])]
)

# PythonScripts product
setup(
    name='PythonScripts',
    author=AUTHOR,

    packages=['Products.PythonScripts', 'Products.PythonScripts.Extensions',
              'Products.PythonScripts.help', 'Products.PythonScripts.tests'],

    data_files=[['Products/PythonScripts', ['Products/PythonScripts/*.txt']],
                ['Products/PythonScripts/help',
                    ['Products/PythonScripts/help/*.stx']],
                ['Products/PythonScripts/tests/tscripts',
                    ['Products/PythonScripts/tests/tscripts/*']],
                ['Products/PythonScripts/www',
                    ['Products/PythonScripts/www/*']]],
    cmdclass={'install_data': install_data}
)

# Sessions product
setup(
    name='Sessions',
    author=AUTHOR,

    packages=['Products.Sessions', 'Products.Sessions.help',
              'Products.Sessions.tests', 'Products.Sessions.stresstests'],

    data_files=[['Products/Sessions/help', ['Products/Sessions/help/*.stx']],
                ['Products/Sessions/dtml', ['Products/Sessions/dtml/*']],
                ['Products/Sessions/www', ['Products/Sessions/www/*']]],
    cmdclass={'install_data': install_data}
)

# SiteAccess product
setup(
    name='SiteAccess',
    author=AUTHOR,

    packages=['Products.SiteAccess', 'Products.SiteAccess.Extensions'],

    data_files=[['Products/SiteAccess', ['Products/SiteAccess/*.txt']],
                ['Products/SiteAccess/doc', ['Products/SiteAccess/doc/*']],
                ['Products/SiteAccess/help', ['Products/SiteAccess/help/*']],
                ['Products/SiteAccess/www', ['Products/SiteAccess/www/*']]],
    cmdclass={'install_data': install_data}
)

# SiteErrorLog product
setup(
    name='SiteErrorLog',
    author=AUTHOR,

    packages=['Products.SiteErrorLog'],

    data_files=[['Products/SiteErrorLog/www',
        ['Products/SiteErrorLog/www/*']]],
    cmdclass={'install_data': install_data}
)

# StandardCacheManagers product
setup(
    name='StandardCacheManagers',
    author=AUTHOR,

    packages=['Products.StandardCacheManagers'],

    data_files=[['Products/StandardCacheManagers',
                    ['Products/StandardCacheManagers/*.txt',
                     'Products/StandardCacheManagers/*.gif']],
                ['Products/StandardCacheManagers/dtml',
                    ['Products/StandardCacheManagers/dtml/*']],
                ['Products/StandardCacheManagers/help',
                    ['Products/StandardCacheManagers/help/*']]],
    cmdclass={'install_data': install_data}
)

# TemporaryFolder product
setup(
    name='TemporaryFolder',
    author=AUTHOR,

    packages=['Products.TemporaryFolder', 'Products.TemporaryFolder.tests'],

    data_files=[['Products/TemporaryFolder/dtml',
                    ['Products/TemporaryFolder/dtml/*']],
                ['Products/TemporaryFolder/help',
                    ['Products/TemporaryFolder/help/*']],
                ['Products/TemporaryFolder/www',
                    ['Products/TemporaryFolder/www/*']]],
    cmdclass={'install_data': install_data}
)

# Transience product
setup(
    name='Transience',
    author=AUTHOR,

    packages=['Products.Transience', 'Products.Transience.help',
              'Products.Transience.tests'],

    data_files=[['Products/Transience', ['Products/Transience/*.stx']],
		['Products/Transience/dtml', ['Products/Transience/dtml/*']],
                ['Products/Transience/help',
                    ['Products/Transience/help/*.stx']],
                ['Products/Transience/www', ['Products/Transience/www/*']]],
    cmdclass={'install_data': install_data}
)

# ZCatalog product
setup(
    name='ZCatalog',
    author=AUTHOR,

    packages=['Products.ZCatalog', 'Products.ZCatalog.help',
              'Products.ZCatalog.regressiontests', 'Products.ZCatalog.tests'],

    data_files=[['Products/ZCatalog', ['Products/ZCatalog/*.gif',
                                       'Products/ZCatalog/*.txt']],
                ['Products/ZCatalog/dtml', ['Products/ZCatalog/dtml/*']],
                ['Products/ZCatalog/help', ['Products/ZCatalog/help/*.stx']],
                ['Products/ZCatalog/www', ['Products/ZCatalog/www/*']]],
    cmdclass={'install_data': install_data}
)

# ZCTextIndex product
setup(
    name='ZCTextIndex',
    author=AUTHOR,

    ext_modules=[
	Extension(name='Products.ZCTextIndex.stopper',
	          sources=['Products/ZCTextIndex/stopper.c']),
	Extension(name='Products.ZCTextIndex.okascore',
		  sources=['Products/ZCTextIndex/okascore.c'])],

    packages=['Products.ZCTextIndex', 'Products.ZCTextIndex.tests'],

    data_files=[['Products/ZCTextIndex', ['Products/ZCTextIndex/README.txt']],
		['Products/ZCTextIndex/dtml', ['Products/ZCTextIndex/dtml/*']],
		['Products/ZCTextIndex/help', ['Products/ZCTextIndex/help/*']],
		['Products/ZCTextIndex/tests',
		    ['Products/ZCTextIndex/tests/python.txt']],
		['Products/ZCTextIndex/www', ['Products/ZCTextIndex/www/*']]],
    cmdclass={'install_data': install_data}
)

# ZGadflyDA product
setup(
    name='ZGadflyDA',
    author=AUTHOR,

    packages=['Products.ZGadflyDA', 'Products.ZGadflyDA.gadfly'],

    data_files=[['Products/ZGadflyDA', ['Products/ZGadflyDA/*.txt']],
                ['Products/ZGadflyDA/dtml', ['Products/ZGadflyDA/dtml/*']],
                ['Products/ZGadflyDA/icons', ['Products/ZGadflyDA/icons/*']],
                ['Products/ZGadflyDA/gadfly',
                    ['Products/ZGadflyDA/gadfly/COPYRIGHT',
                     'Products/ZGadflyDA/gadfly/sql.mar',
                     'Products/ZGadflyDA/gadfly/*.html']]],
    cmdclass={'install_data': install_data}
)

# ZSQLMethods product
setup(
    name='ZSQLMethods',
    author=AUTHOR,

    packages=['Products.ZSQLMethods', 'Products.ZSQLMethods.help'],

    data_files=[['Products/ZSQLMethods', ['Products/ZSQLMethods/*.txt',
                                          'Products/ZSQLMethods/*.gif']],
                ['Products/ZSQLMethods/dtml', ['Products/ZSQLMethods/dtml/*']],
                ['Products/ZSQLMethods/help',
                    ['Products/ZSQLMethods/help/*.stx']]],
    cmdclass={'install_data': install_data}
)

# ZopeTutorial product
setup(
    name='ZopeTutorial',
    author=AUTHOR,

    packages=['Products.ZopeTutorial'],

    data_files=[['Products/ZopeTutorial', ['Products/ZopeTutorial/*.txt',
                                           'Products/ZopeTutorial/*.stx']],
                ['Products/ZopeTutorial/dtml',
                    ['Products/ZopeTutorial/dtml/*']]],
    cmdclass={'install_data': install_data}
)

# Call distutils setup with all lib/python packages and modules, and
# flush setup_info.  Wondering why we run py_modules separately?  So am I.
# Distutils won't let us specify packages and py_modules in the same call.

distutils_setup(
    name='Zope',
    author=AUTHOR,

    packages=setup_info.get('packages', []),
    data_files=setup_info.get('data_files', []),

    headers=setup_info.get('headers', []),
    ext_modules=setup_info.get('ext_modules', []),

    cmdclass={'install_data': install_data}
)
distutils_setup(
    name='Zope',
    author=AUTHOR,

    py_modules=setup_info.get('py_modules', [])
)
setup_info = {}

# The rest of these modules live in the root of the source tree
os.chdir(ZOPE_ROOT)

# ZServer
setup(
    name='ZServer',
    author=AUTHOR,

    packages=['ZServer', 'ZServer.PubCore', 'ZServer.medusa',
              'ZServer.medusa.contrib', 'ZServer.medusa.demo',
              'ZServer.medusa.misc', 'ZServer.medusa.script_handler_demo',
              'ZServer.medusa.sendfile', 'ZServer.medusa.test',
              'ZServer.medusa.thread'],

    data_files=[['ZServer', ['ZServer/*.txt']],
                ['ZServer/medusa', ['ZServer/medusa/*.txt',
                                    'ZServer/medusa/*.html']],
                ['ZServer/medusa/dist', ['ZServer/medusa/dist/*']],
                ['ZServer/medusa/docs', ['ZServer/medusa/docs/*']],
                ['ZServer/medusa/notes', ['ZServer/medusa/notes/*']],
                ['ZServer/medusa/script_handler_demo',
                    ['ZServer/medusa/script_handler_demo/*.mpy']],
                ['ZServer/medusa/sendfile',
                    ['ZServer/medusa/sendfile/README']],
                ['ZServer/medusa/test', ['ZServer/medusa/test/*.txt']]],
    cmdclass={'install_data': install_data},

# Does not work on all platforms... not like we ever compiled it before
# anyway
#
#    ext_modules=[
#       Extension(name='ZServer.medusa.sendfile.sendfilemodule',
#                 sources=['ZServer/medusa/sendfile/sendfilemodule.c'])]

)

# z2.py
setup(
    name='z2.py',
    author=AUTHOR,

    py_modules=['z2']
)

# zpasswd
setup(
    name='zpasswd',
    author=AUTHOR,

    py_modules=['zpasswd']
)

# Default imports
setup(
    name='Zope default imports',
    author=AUTHOR,

    data_files=[['import', ['import/*.zexp']]],
    cmdclass={'install_data': install_data}
)

# And now, the root-level stuff

distutils_setup(
    name='Zope',
    author=AUTHOR,

    packages=setup_info.get('packages', []),
    data_files=setup_info.get('data_files', []),

    headers=setup_info.get('headers', []),
    ext_modules=setup_info.get('ext_modules', []),

    cmdclass={'install_data': install_data}
)
distutils_setup(
    name='Zope',
    author=AUTHOR,

    py_modules=setup_info.get('py_modules', [])
)
