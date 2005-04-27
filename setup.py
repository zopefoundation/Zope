
#!/usr/bin/env python2.3

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

import distutils.core
from distutils.core import Extension

# This function collects setup information for one massive distutils
# run to be done at the end of the script.  If you're making a setup.py
# to use modules from Zope separately, you should be able to cut-and-paste
# the individual setup calls out into your own setup.py and it should
# Just Work(tm).

setup_info = {}
def setup(name=None, author=None, cmdclass=None, **kwargs):
    for keyword in kwargs.keys():
        if not setup_info.has_key(keyword):
            setup_info[keyword] = []
        setup_info[keyword] += kwargs[keyword]

# Override install_data to install into module directories, and to support
# globbing on data_files.

from distutils.command.install import install
from distutils.command.install_data import install_data
from distutils.util import convert_path

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

EXTENSIONCLASS_INCLUDEDIRS = ['ExtensionClass']


# AccessControl
setup(
    name='AccessControl',
    author=AUTHOR,

    packages=['AccessControl',
              'AccessControl.tests', 'AccessControl.tests.mixed_module',
              'AccessControl.tests.mixed_module.submodule',
              'AccessControl.tests.private_module',
              'AccessControl.tests.private_module.submodule',
              'AccessControl.tests.public_module',
              'AccessControl.tests.public_module.submodule'],
    data_files=[['AccessControl', ['AccessControl/*.txt']],
                ['AccessControl/dtml', ['AccessControl/dtml/*']],
                ['AccessControl/securitySuite',
                    ['AccessControl/securitySuite/README',
                     'AccessControl/securitySuite/*.py']],
                ['AccessControl/www', ['AccessControl/www/*']]],
    ext_modules=[
        Extension(name='AccessControl.cAccessControl',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS+['Acquisition'],
                  sources=['AccessControl/cAccessControl.c'],
                  depends=['ExtensionClass/ExtensionClass.h',
                           'ExtensionClass/pickle/pickle.c',
                           'Acquisition/Acquisition.h'],
                  )]
    )

# App
setup(
    name='App',
    author=AUTHOR,

    packages=['App', 'App.tests'],
    data_files=[['App/dtml', ['App/dtml/*']],
                ['App/www', ['App/www/*']]],
    )

# BTrees
setup(
    name='BTrees',
    author=AUTHOR,

    packages=['BTrees', 'BTrees.tests'],
    ext_modules=[
        Extension(name='BTrees._OOBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['persistent'],
                  sources=['BTrees/_OOBTree.c']),
        Extension(name='BTrees._OIBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['persistent'],
                  sources=['BTrees/_OIBTree.c']),
        Extension(name='BTrees._IIBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['persistent'],
                  define_macros=[('EXCLUDE_INTSET_SUPPORT', None)],
                  sources=['BTrees/_IIBTree.c']),
        Extension(name='BTrees._IOBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['persistent'],
                  define_macros=[('EXCLUDE_INTSET_SUPPORT', None)],
                  sources=['BTrees/_IOBTree.c']),
        Extension(name='BTrees._IFBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['persistent'],
                  define_macros=[('EXCLUDE_INTSET_SUPPORT', None)],
                  sources=['BTrees/_IFBTree.c']),
        Extension(name='BTrees._fsBTree',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS + ['persistent'],
                  define_macros=[('EXCLUDE_INTSET_SUPPORT', None)],
                  sources=['BTrees/_fsBTree.c'])],
    data_files=[['BTrees', ['BTrees/Maintainer.txt']]],
    )


# DateTime
setup(
    name='DateTime',
    author=AUTHOR,

    packages=['DateTime', 'DateTime.tests'],
    data_files=[['DateTime', ['DateTime/DateTime.txt']],
                ['DateTime/tests', ['DateTime/tests/julian_testdata.txt.gz']]],
    )

# DBTab
setup(
    name='DBTab',
    author=AUTHOR,

    packages=['DBTab'],
    data_files=[['DBTab', ['DBTab/CHANGES.txt']]],
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
    ext_modules=[
        Extension(name='DocumentTemplate.cDocumentTemplate',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=['DocumentTemplate/cDocumentTemplate.c'])]
    )

# docutils
setup(
    name='docutils',
    author='David Goodger and contributors',
    packages=['docutils', 'docutils.languages', 'docutils.parsers',
              'docutils.parsers.rst', 'docutils.parsers.rst.directives',
              'docutils.parsers.rst.languages', 'docutils.readers',
              'docutils.transforms', 'docutils.writers'],
    )

# ExtensionClass
setup(
    name='ExtensionClass',
    author=AUTHOR,

    packages=['ExtensionClass', 'Acquisition', 'MethodObject', 'MultiMapping',
              'ThreadLock', 'Missing', 'Record', 'ComputedAttribute'],

    ext_modules=[
        Extension(name='ExtensionClass._ExtensionClass',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=["ExtensionClass/_ExtensionClass.c"],
                  depends=["ExtensionClass/ExtensionClass.h"],
                  ),
        Extension(name='Acquisition._Acquisition',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=["Acquisition/_Acquisition.c"],
                  depends=["ExtensionClass/ExtensionClass.h",
                           "Acquisition/Acquisition.h"],
                  ),
        Extension(name='MethodObject._MethodObject',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=["MethodObject/_MethodObject.c"],
                  depends=["ExtensionClass/ExtensionClass.h"],
                  ),
        Extension(name='MultiMapping._MultiMapping',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=["MultiMapping/_MultiMapping.c"],
                  depends=["ExtensionClass/ExtensionClass.h"],
                  ),
        Extension(name='ThreadLock._ThreadLock',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=["ThreadLock/_ThreadLock.c"],
                  depends=["ExtensionClass/ExtensionClass.h"],
                  ),
        Extension(name='Missing._Missing',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=["Missing/_Missing.c"],
                  depends=["ExtensionClass/ExtensionClass.h"],
                  ),
        Extension(name='Record._Record',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=["Record/_Record.c"],
                  depends=["ExtensionClass/ExtensionClass.h"],
                  ),
        Extension(name='ComputedAttribute._ComputedAttribute',
                  include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
                  sources=["ComputedAttribute/_ComputedAttribute.c"],
                  depends=["ExtensionClass/ExtensionClass.h"],
                  ),
        ]
    )

# HelpSys
setup(
    name='HelpSys',
    author=AUTHOR,

    packages=['HelpSys'],
    data_files=[['HelpSys/dtml', ['HelpSys/dtml/*']],
                ['HelpSys/images', ['HelpSys/images/*']]],
    )

# Interface
setup(
    name='Interface',
    author=AUTHOR,

    packages=['Interface', 'Interface.tests',
              'Interface.Common', 'Interface.Common.tests'],
    )

#nt_svcutils
setup(
    name='nt_svcutils',
    author=AUTHOR,
    packages=['nt_svcutils'],
    )

# OFS
setup(
    name='OFS',
    author=AUTHOR,

    packages=['OFS', 'OFS.tests'],
    data_files=[['OFS', ['OFS/mime.types']],
                ['OFS/tests',
                    ['OFS/tests/mime.types-?',
                     'OFS/tests/*.gif']],
                ['OFS/dtml', ['OFS/dtml/*']],
                ['OFS/standard', ['OFS/standard/*']],
                ['OFS/www', ['OFS/www/*']]],
    )

# reStructuredText
setup(
    name='reStructuredText',
    author='Andreas Jung',

    packages=['reStructuredText', 'reStructuredText.tests'],
    data_files=[['reStructuredText', ['reStructuredText/*.txt']],
               ],
    )


# RestrictedPython
setup(
    name='RestrictedPython',
    author=AUTHOR,

    packages=['RestrictedPython', 'RestrictedPython.tests'],
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
    )

# StructuredText
setup(
    name='StructuredText',
    author=AUTHOR,

    packages=['StructuredText', 'StructuredText.tests'],
    data_files=[['StructuredText', ['StructuredText/*.txt']],
                ['StructuredText/regressions',
                    ['StructuredText/regressions/*.py',
                     'StructuredText/regressions/*.ref',
                     'StructuredText/regressions/*.stx']]],
    )


# Signals
setup(
    name='Signals',
    author=AUTHOR,

    packages=['Signals'],
    )

# ZRDB
setup(
    name='ZRDB',
    author=AUTHOR,

    packages=['Shared.DC.ZRDB'],
    data_files=[['Shared/DC/ZRDB/dtml', ['Shared/DC/ZRDB/dtml/*']],
                ['Shared/DC/ZRDB/www', ['Shared/DC/ZRDB/www/*']]],
    )

# dcpyexpat
PYEXPAT_DIR=os.path.join(PACKAGES_ROOT, 'Shared', 'DC', 'xml', 'pyexpat')
DCPYEXPAT_INCLUDEDIRS=[os.path.join(PYEXPAT_DIR, 'expat', 'xmlparse'),
                       os.path.join(PYEXPAT_DIR, 'expat', 'xmltok')]
DCPYEXPAT_DIR='Shared/DC/xml/pyexpat'

setup(
    name='dcpyexpat',
    author=AUTHOR,

    packages=['Shared.DC.xml', 'Shared.DC.xml.pyexpat'],
    data_files=[['Shared/DC/xml/pyexpat', ['Shared/DC/xml/pyexpat/README']]],
    ext_modules=[
        Extension(name='Shared.DC.xml.pyexpat.dcpyexpat',
                  include_dirs=DCPYEXPAT_INCLUDEDIRS,
                  define_macros=[('XML_NS', None)],
                  sources=[DCPYEXPAT_DIR + '/expat/xmlparse/xmlparse.c',
                           DCPYEXPAT_DIR + '/expat/xmlparse/hashtable.c',
                           DCPYEXPAT_DIR + '/expat/xmltok/xmlrole.c',
                           DCPYEXPAT_DIR + '/expat/xmltok/xmltok.c',
                           DCPYEXPAT_DIR + '/dcpyexpat.c'])]
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
    )

# tempstorage
setup(
    name='tempstorage',
    author=AUTHOR,

    packages=['tempstorage', 'tempstorage.tests'],
    data_files=[['tempstorage', ['tempstorage/*.xml']]],
    )

# Testing
setup(
    name='Testing',
    author=AUTHOR,

    packages=['Testing', 'Testing.ZopeTestCase',
              'Testing.ZopeTestCase.zopedoctest'],
    data_files=[['Testing', ['Testing/README.txt']],
                ['Testing/var', ['Testing/var/README.txt']],
                ['Testing/ZopeTestCase/doc', ['Testing/ZopeTestCase/doc/*']],
                ['Testing/ZopeTestCase/zopedoctest',
                    ['Testing/ZopeTestCase/zopedoctest/*.txt']]],
    )

# ThreadedAsync
setup(
    name='ThreadedAsync',
    author=AUTHOR,

    packages=['ThreadedAsync'],
    )

# TreeDisplay
setup(
    name='TreeDisplay',
    author=AUTHOR,

    packages=['TreeDisplay'],
    data_files=[['TreeDisplay/www', ['TreeDisplay/www/*']]],
    )

# ZClasses
setup(
    name='ZClasses',
    author=AUTHOR,

    packages=['ZClasses'],
    data_files=[['ZClasses', ['ZClasses/*.gif', 'ZClasses/*.txt',
                              'ZClasses/*.fs']],
                ['ZClasses/dtml', ['ZClasses/dtml/*']]],
    )


# ZODB
setup(
    name='ZODB',
    author=AUTHOR,

    packages=['Persistence', 'Persistence.tests',
              'persistent', 'persistent.tests',
              'transaction', 'transaction.tests',
              'ZODB', 'ZODB.FileStorage', 'ZODB.tests'],
    data_files=[['persistent/tests', ['persistent/tests/*.txt']],
                ['transaction', ['transaction/*.txt']],
                ['ZODB', ['ZODB/*.txt', 'ZODB/*.xml']],
                ['ZODB/tests', ['ZODB/tests/*.txt']]],
    ext_modules=[
        Extension(name='persistent.cPersistence',
                  include_dirs=['persistent'],
                  sources=['persistent/cPersistence.c',
                           'persistent/ring.c'],
                  depends=['persistent/cPersistence.h',
                           'persistent/ring.h',
                           'persistent/ring.c'],
                  ),
        Extension(name='Persistence._Persistence',
                  include_dirs=['persistent', 'ExtensionClass'],
                  sources=['Persistence/_Persistence.c',
                           ],
                  depends=['persistent/cPersistence.h',
                           'ExtensionClass/ExtensionClass.h',
                           ],
                  ),
        Extension(name='persistent.cPickleCache',
                  include_dirs=['persistent'],
                  sources=['persistent/cPickleCache.c',
                           'persistent/ring.c'],
                  depends = ['persistent/cPersistence.h',
                             'persistent/ring.h',
                             'persistent/ring.c']
                  ),
        Extension(name='persistent.TimeStamp',
                  include_dirs=['persistent'],
                  sources=['persistent/TimeStamp.c']),
        # XXX We need to rewrite this soon.
##        Extension(name='ZODB.coptimizations',
##                  include_dirs=['persistent'],
##                  sources=['ZODB/coptimizations.c']),
        Extension(name='ZODB.winlock',
                  include_dirs=['persistent'],
                  sources=['ZODB/winlock.c'])],
    )

# ZPublisher
setup(
    name='ZPublisher',
    author=AUTHOR,

    packages=['ZPublisher', 'ZPublisher.tests'],
    )

# ZTUtils
setup(
    name='ZTUtils',
    author=AUTHOR,

    packages=['ZTUtils', 'ZTUtils.tests'],
    data_files=[['ZTUtils', ['ZTUtils/*.txt']]],
    )

# Zope
setup(
    name='Zope',
    author=AUTHOR,

    py_modules=['Zope'],
    packages=['Zope2', 'Zope2.App', 'Zope2.Startup', 'Zope2.Startup.misc',
              'Zope2.Startup.nt', 'Zope2.Startup.tests'],
    data_files=[ ['Zope2/Startup', ['Zope2/Startup/*.xml']] ],
    )

# webdav
setup(
    name='webdav',
    author=AUTHOR,

    packages=['webdav'],
    data_files=[['webdav/dtml', ['webdav/dtml/*']],
                ['webdav/www', ['webdav/www/*']]],
    )

# zExceptions
setup(
    name='zExceptions',
    author=AUTHOR,

    packages=['zExceptions', 'zExceptions.tests'],
    )

# zLOG
setup(
    name='zLOG',
    author=AUTHOR,

    packages=['zLOG', 'zLOG.tests'],
    )

# zdaemon
setup(
    name='zdaemon',
    author=AUTHOR,

    packages=['zdaemon', 'zdaemon.tests'],
    data_files=[['zdaemon', ['zdaemon/sample.conf',
                             'zdaemon/component.xml',
                             'zdaemon/schema.xml']],
                ['zdaemon/tests', ['zdaemon/tests/donothing.sh']]]
    )


# initgroups
setup(
    name='initgroups',
    author=AUTHOR,

    ext_modules=[
        Extension(name='initgroups',
                  sources=['../Components/initgroups/initgroups.c'])]
    )

# ZopeUndo
setup(
    name='ZopeUndo',
    author=AUTHOR,

    packages=['ZopeUndo', 'ZopeUndo.tests'],
    )

# ZEO
setup(
    name='ZEO',
    author=AUTHOR,

    packages=['ZEO', 'ZEO.auth', 'ZEO.tests', 'ZEO.zrpc'],
    data_files=[['ZEO', ['ZEO/*.txt', 'ZEO/*.xml']]],
    )

# ZConfig
setup(
    name='ZConfig',
    author=AUTHOR,

    packages=['ZConfig', 'ZConfig.tests',
              'ZConfig.tests.library', 'ZConfig.tests.library.widget',
              'ZConfig.tests.library.thing',
              'ZConfig.components',
              'ZConfig.components.basic', 'ZConfig.components.basic.tests',
              'ZConfig.components.logger', 'ZConfig.components.logger.tests',
              ],
    data_files=[
        ['../../doc/zconfig',
         ['ZConfig/doc/zconfig.pdf', 'ZConfig/doc/schema.dtd']],
        ['ZConfig/components/basic', ['ZConfig/components/basic/*.xml']],
        ['ZConfig/components/logger', ['ZConfig/components/logger/*.xml']],
        ['ZConfig/tests/input', ['ZConfig/tests/input/*']],
        ['ZConfig/tests/library/thing', ['ZConfig/tests/library/thing/*']],
        ['ZConfig/tests/library/thing/extras',
         ['ZConfig/tests/library/thing/extras/*']],
        ['ZConfig/tests/library/widget', ['ZConfig/tests/library/widget/*']],
        ['ZConfig/scripts', ['ZConfig/scripts/zconfig']],
        ],
    )

# Other top-level packages (XXX should these be broken out at all?)
setup(
    name='Top-level',
    author=AUTHOR,

    py_modules=['Globals', 'ImageFile', 'Lifetime'],
    data_files=[['.',['version.txt']]],
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

    packages=['Products.ExternalMethod', 'Products.ExternalMethod.tests'],
    data_files=[['Products/ExternalMethod',
                    ['Products/ExternalMethod/*.gif',
                     'Products/ExternalMethod/*.txt']],
                ['Products/ExternalMethod/dtml',
                    ['Products/ExternalMethod/dtml/*']],
                ['Products/ExternalMethod/help',
                    ['Products/ExternalMethod/help/*']],
                ['Products/ExternalMethod/tests/Extensions',
                    ['Products/ExternalMethod/tests/Extensions/*.py']],
                ['Products/ExternalMethod/www',
                    ['Products/ExternalMethod/www/*']]],
    )

# MIMETools product
setup(
    name='MIMETools',
    author=AUTHOR,

    packages=['Products.MIMETools'],
    data_files=[['Products/MIMETools', ['Products/MIMETools/*.txt']]],
    )

# MailHost product
setup(
    name='MailHost',
    author=AUTHOR,

    packages=['Products.MailHost', 'Products.MailHost.tests'],
    data_files=[['Products/MailHost', ['Products/MailHost/*.txt']],
                ['Products/MailHost/dtml', ['Products/MailHost/dtml/*']],
                ['Products/MailHost/help', ['Products/MailHost/help/*.py',
                                            'Products/MailHost/help/*.stx']],
                ['Products/MailHost/www', ['Products/MailHost/www/*']]],
    )

# OFSP product
setup(
    name='OFSP',
    author=AUTHOR,

    packages=['Products.OFSP'],
    data_files=[['Products/OFSP', ['Products/OFSP/*.txt']],
                ['Products/OFSP/dtml', ['Products/OFSP/dtml/*']],
                ['Products/OFSP/help', ['Products/OFSP/help/*.py',
                                        'Products/OFSP/help/*.stx']],
                ['Products/OFSP/images', ['Products/OFSP/images/*']]],
    )

# PageTemplates product
setup(
    name='PageTemplates',
    author=AUTHOR,

    packages=['Products.PageTemplates', 'Products.PageTemplates.tests'],

    data_files=[['Products/PageTemplates', ['Products/PageTemplates/*.txt']],
                ['Products/PageTemplates/examples',
                    ['Products/PageTemplates/examples/*']],
                ['Products/PageTemplates/help',
                    ['Products/PageTemplates/help/*.py',
                     'Products/PageTemplates/help/*.stx']],
                ['Products/PageTemplates/tests/input',
                    ['Products/PageTemplates/tests/input/*']],
                ['Products/PageTemplates/tests/output',
                    ['Products/PageTemplates/tests/output/*']],
                ['Products/PageTemplates/www',
                    ['Products/PageTemplates/www/*']]],
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

    ext_modules=[
        Extension(name='Products.PluginIndexes.TextIndex.Splitter.ZopeSplitter.ZopeSplitter',
                  sources=['Products/PluginIndexes/TextIndex/Splitter/ZopeSplitter/src/ZopeSplitter.c']),
        Extension(name='Products.PluginIndexes.TextIndex.Splitter.ISO_8859_1_Splitter.ISO_8859_1_Splitter',
                  sources=['Products/PluginIndexes/TextIndex/Splitter/ISO_8859_1_Splitter/src/ISO_8859_1_Splitter.c']),
        Extension(name='Products.PluginIndexes.TextIndex.Splitter.UnicodeSplitter.UnicodeSplitter',
                  sources=['Products/PluginIndexes/TextIndex/Splitter/UnicodeSplitter/src/UnicodeSplitter.c'])],
    )

# PythonScripts product
setup(
    name='PythonScripts',
    author=AUTHOR,

    packages=['Products.PythonScripts', 'Products.PythonScripts.tests'],
    data_files=[['Products/PythonScripts', ['Products/PythonScripts/*.txt']],
                ['Products/PythonScripts/Extensions',
                    ['Products/PythonScripts/Extensions/*.py']],
                ['Products/PythonScripts/help',
                    ['Products/PythonScripts/help/*.py',
                     'Products/PythonScripts/help/*.stx']],
                ['Products/PythonScripts/tests/tscripts',
                    ['Products/PythonScripts/tests/tscripts/*']],
                ['Products/PythonScripts/www',
                    ['Products/PythonScripts/www/*']]],
    )

# Sessions product
setup(
    name='Sessions',
    author=AUTHOR,

    packages=['Products.Sessions', 'Products.Sessions.tests'],
    data_files=[['Products/Sessions/help', ['Products/Sessions/help/*.py',
                                            'Products/Sessions/help/*.stx']],
                ['Products/Sessions/dtml', ['Products/Sessions/dtml/*']],
                ['Products/Sessions/stresstests',
                     ['Products/Sessions/stresstests/*.py']],
                ['Products/Sessions/www', ['Products/Sessions/www/*']]],
    )

# SiteAccess product
setup(
    name='SiteAccess',
    author=AUTHOR,

    packages=['Products.SiteAccess', 'Products.SiteAccess.tests'],
    data_files=[['Products/SiteAccess', ['Products/SiteAccess/*.txt']],
                ['Products/SiteAccess/doc', ['Products/SiteAccess/doc/*']],
                ['Products/SiteAccess/Extensions',
                     ['Products/SiteAccess/Extensions/*.py']],
                ['Products/SiteAccess/help', ['Products/SiteAccess/help/*']],
                ['Products/SiteAccess/www', ['Products/SiteAccess/www/*']]],
    )

# SiteErrorLog product
setup(
    name='SiteErrorLog',
    author=AUTHOR,

    packages=['Products.SiteErrorLog'],
    data_files=[['Products/SiteErrorLog/www',
                 ['Products/SiteErrorLog/www/*']]],
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
    )

# TemporaryFolder product
setup(
    name='TemporaryFolder',
    author=AUTHOR,

    packages=['Products.TemporaryFolder', 'Products.TemporaryFolder'],
    data_files=[['Products/TemporaryFolder/dtml',
                    ['Products/TemporaryFolder/dtml/*']],
                ['Products/TemporaryFolder/help',
                    ['Products/TemporaryFolder/help/*']],
                ['Products/TemporaryFolder/www',
                    ['Products/TemporaryFolder/www/*']]],
    )

# Transience product
setup(
    name='Transience',
    author=AUTHOR,

    packages=['Products.Transience', 'Products.Transience.tests'],
    data_files=[['Products/Transience', ['Products/Transience/*.stx']],
                ['Products/Transience/dtml', ['Products/Transience/dtml/*']],
                ['Products/Transience/help',
                    ['Products/Transience/help/*.py',
                     'Products/Transience/help/*.stx']],
                ['Products/Transience/www', ['Products/Transience/www/*']]],
    )

# ZCatalog product
setup(
    name='ZCatalog',
    author=AUTHOR,

    packages=['Products.ZCatalog', 'Products.ZCatalog.tests'],
    data_files=[['Products/ZCatalog',
                     ['Products/ZCatalog/*.gif', 'Products/ZCatalog/*.txt']],
                ['Products/ZCatalog/regressiontests',
                     ['Products/ZCatalog/regressiontests/*.py']],
                ['Products/ZCatalog/dtml', ['Products/ZCatalog/dtml/*']],
                ['Products/ZCatalog/help', ['Products/ZCatalog/help/*.stx',
                                            'Products/ZCatalog/help/*.py']],
                ['Products/ZCatalog/www', ['Products/ZCatalog/www/*']]],
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
    )

# ZODBMountPoint product
setup(
    name='ZODBMountPoint',
    author=AUTHOR,

    packages=['Products.ZODBMountPoint', 'Products.ZODBMountPoint.tests'],
    data_files=[['Products/ZODBMountPoint/www',
                 ['Products/ZODBMountPoint/www/*']],
                ],
    )

# ZReST product
setup(
    name='ZReST ',
    author='Richard Jones',

    packages=['Products.ZReST'],
    data_files=[['Products/ZReST', ['Products/ZReST/*.txt']],
                ['Products/ZReST/dtml', ['Products/ZReST/dtml/*']],
                ['Products/ZReST/www', ['Products/ZReST/www/*']],
                ],
    )

# ZSQLMethods product
setup(
    name='ZSQLMethods',
    author=AUTHOR,

    packages=['Products.ZSQLMethods'],
    data_files=[['Products/ZSQLMethods', ['Products/ZSQLMethods/*.txt',
                                          'Products/ZSQLMethods/*.gif']],
                ['Products/ZSQLMethods/dtml', ['Products/ZSQLMethods/dtml/*']],
                ['Products/ZSQLMethods/help',
                    ['Products/ZSQLMethods/help/*.stx',
                     'Products/ZSQLMethods/help/*.py']]],
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
    )

# ZServer
setup(
    name='ZServer',
    author=AUTHOR,

    packages=['ZServer', 'ZServer.PubCore', 'ZServer.tests', 'ZServer.medusa',
              'ZServer.medusa.test',
              'ZServer.medusa.thread'],
    data_files=[['ZServer', ['ZServer/*.txt', 'ZServer/*.xml']],
                ['ZServer/medusa/dist', ['ZServer/medusa/dist/*']],
                ['ZServer/medusa/docs', ['ZServer/medusa/docs/*']],
                ['ZServer/medusa/test', ['ZServer/medusa/test/*.txt']]],
    )


setup(
    name='Five',
    author='Martijn Faassen',

    packages=['Products.Five',
              'Products.Five.tests',
              'Products.Five.tests.products',
              'Products.Five.tests.products.FiveTest'],
    data_files=[['Products/Five', ['Products/Five/*']],
                ['Products/Five/doc', ['Products/Five/doc/*']],
                ['Products/Five/skel', ['Products/Five/skel/*']],
                ['Products/Five/tests', ['Products/Five/tests/*']],
                ['Products/Five/tests/products/FiveTest',
                    ['Products/Five/tests/products/FiveTest/*']],
                ['Products/Five/tests/products/FiveTest/pages',
                    ['Products/Five/tests/products/FiveTest/pages/*']],
                ['Products/Five/tests/products/FiveTest/www',
                    ['Products/Five/tests/products/FiveTest/www/*']],
                ],
    )



# Zope 3 / Five integration layer support. Note that in addition to the
# Five package itself, we also pull in several modules from the Zope 3
# heirarchy: zope, persistent, transaction. Most of this is ripped from
# the Zope 3 setup.py.

from distutils import dir_util
from distutils.command.build import build as buildcmd
from distutils.command.build_ext import build_ext
from distutils.command.install_lib import install_lib as installcmd
from distutils.core import setup
from distutils.dist import Distribution
from distutils.extension import Extension

if sys.version_info < (2, 3):
    _setup = setup
    def setup(**kwargs):
        if kwargs.has_key("classifiers"):
            del kwargs["classifiers"]
        _setup(**kwargs)


# A hack to determine if Extension objects support the `depends' keyword arg,
# which only exists in Python 2.3's distutils.
if not "depends" in Extension.__init__.func_code.co_varnames:
    # If it doesn't, create a local replacement that removes depends from the
    # kwargs before calling the regular constructor.
    _Extension = Extension
    class Extension(_Extension):
        def __init__(self, name, sources, **kwargs):
            if "depends" in kwargs:
                del kwargs["depends"]
            _Extension.__init__(self, name, sources, **kwargs)


# We have to snoop for file types that distutils doesn't copy correctly when
# doing a non-build-in-place.
EXTS = ['.conf', '.css', '.dtd', '.gif', '.jpg', '.html',
        '.js',   '.mo',  '.png', '.pt', '.stx', '.ref',
        '.txt',  '.xml', '.zcml', '.mar', '.in', '.sample',
        '.rst',  '.request', '.response',
        ]

ONESHOTS = [# zope/app/publisher/browser/tests/testfiles/
            # has a file named plain 'png', with no extension.
            'png',
           ]

IGNORE_NAMES = (
    'CVS', '.svn', # Revision Control Directories
    )

# This class serves multiple purposes.  It walks the file system looking for
# auxiliary files that distutils doesn't install properly, and it actually
# copies those files (when hooked into by distutils).  It also walks the file
# system looking for candidate packages for distutils to install as normal.
# The key here is that the package must have an __init__.py file.
class Finder:
    def __init__(self, exts, prefix):
        self._files = []
        self._pkgs = {}
        self._exts = exts
        # We're finding packages in lib/python in the source dir, but we're
        # copying them directly under build/lib.<plat>.  So we need to lop off
        # the prefix when calculating the package names from the file names.
        prefix, rest = os.path.split(prefix)
        self._plen = len(prefix) + 1

    def visit(self, ignore, dir, files):
        # Remove ignored filenames
        for ignore in IGNORE_NAMES:
            if ignore in files:
                files.remove(ignore)
        for fname in files:
            # First see if this is one of the packages we want to add, or if
            # we're really skipping this package.
            if '__init__.py' in files:
                aspkg = dir[self._plen:].replace(os.sep, '.')
                self._pkgs[aspkg] = True
            # Add any extra files we're interested in
            base, ext = os.path.splitext(fname)
            if ext in self._exts or fname in ONESHOTS:
                self._files.append(os.path.join(dir, fname))

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

# This bit uses the finder to crawl through the zope3 packages we need
# and Do The Right Thing to arrange for setup for sub-packages.
z3_packages = ['zope']
packages = []

for name in z3_packages:
    basedir = os.path.join(PACKAGES_ROOT, name)
    finder = Finder(EXTS, basedir)
    os.path.walk(basedir, finder.visit, None)
    packages.extend(finder.get_packages())

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
    def run(self):
        os.path.walk(os.curdir, remove_stale_bytecode, None)
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


# All Zope3 extension modules must be listed here.
ext_modules = [

    Extension("zope.proxy._zope_proxy_proxy",
              ["zope/proxy/_zope_proxy_proxy.c"],
              include_dirs = ["zope/proxy"],
              depends = ["zope/proxy/proxy.h"]),

    Extension("zope.security._proxy", ["zope/security/_proxy.c"],
              include_dirs = ["zope/proxy"],
              depends = ["zope/proxy/proxy.h"]),

    Extension("zope.security._zope_security_checker",
              ["zope/security/_zope_security_checker.c"],
              include_dirs = [],
              depends = []),

    Extension("zope.interface._zope_interface_coptimizations",
              ["zope/interface/_zope_interface_coptimizations.c"]),

    Extension("zope.hookable._zope_hookable",
              ["zope/hookable/_zope_hookable.c"]),

    Extension("zope.thread._zope_thread",
              ["zope/thread/_zope_thread.c"]),

    Extension("zope.app.container._zope_app_container_contained",
              ["zope/app/container/_zope_app_container_contained.c"],
              include_dirs = ["persistent",
                              "zope/proxy",
                              "zope/app/container"],
              depends = [
                 "persistent/cPersistence.h",
                 "zope/proxy/_zope_proxy_proxy.c",
                 ]),

    ]

# We're using the module docstring as the distutils descriptions.
doclines = __doc__.split("\n")

setup(name="zopex30",
      version="X3.0",
      maintainer="Zope Corporation",
      maintainer_email="zope3-dev@zope.org",
      url = "http://dev.zope.org/Zope3/",
      ext_modules = ext_modules,
      license = "http://www.zope.org/Resources/ZPL",
      platforms = ["any"],
      description = doclines[0],
      long_description = "\n".join(doclines[2:]),
      packages = packages,
      distclass = MyDistribution,
      )





# Call distutils setup with all lib/python packages and modules, and
# flush setup_info.  Wondering why we run py_modules separately?  So am I.
# Distutils won't let us specify packages and py_modules in the same call.

distutils.core.setup(
    name='Zope',
    author=AUTHOR,

    packages=setup_info.get('packages', []),
    data_files=setup_info.get('data_files', []),
    headers=setup_info.get('headers', []),
    ext_modules=setup_info.get('ext_modules', []),
    scripts=setup_info.get('scripts', []),
    distclass=ZopeDistribution,
    )

distutils.core.setup(
    name='Zope',
    author=AUTHOR,
    py_modules=setup_info.get('py_modules', []),
    distclass=ZopeDistribution,
    )

# The rest of these modules live in the root of the source tree
os.chdir(BASE_DIR)

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
    ["../../import", ['import/*.zexp']],
    ["../../bin", ['utilities/README.txt']],
    ]

os.path.walk("skel", skel_visit, installed_data_files)

distutils.core.setup(
    name='Zope',
    author=AUTHOR,

    data_files=installed_data_files,
    scripts=["utilities/mkzeoinstance.py", "utilities/mkzopeinstance.py",
             "utilities/check_catalog.py", "utilities/load_site.py",
             "utilities/requestprofiler.py", "utilities/zpasswd.py",
             "utilities/copyzopeskel.py", "utilities/reindex_catalog.py",
             "utilities/compilezpy.py", "utilities/decompilezpy.py",
             "utilities/ZODBTools/timeout.py", "utilities/ZODBTools/analyze.py",
             "utilities/ZODBTools/checkbtrees.py", "utilities/ZODBTools/fsdump.py",
             "utilities/ZODBTools/fsrefs.py" , "utilities/ZODBTools/fstail.py",
             "utilities/ZODBTools/fstest.py", "utilities/ZODBTools/migrate.py",
             "utilities/ZODBTools/netspace.py", "utilities/ZODBTools/parsezeolog.py",
             "utilities/ZODBTools/repozo.py", "utilities/ZODBTools/space.py",
             "utilities/ZODBTools/timeout.py", "utilities/ZODBTools/zeopack.py",
             "utilities/ZODBTools/zeoqueue.py", "utilities/ZODBTools/zeoreplay.py",
             "utilities/ZODBTools/zeoserverlog.py", "utilities/ZODBTools/zeoup.py",
             "utilities/ZODBTools/zodbload.py",
             "test.py"],
    distclass=ZopeDistribution,
    )
