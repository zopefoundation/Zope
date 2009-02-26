##############################################################################
#
# Copyright (c) 2007 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Setup for the Acquisition egg package
"""
import os
from setuptools import setup, find_packages, Extension

EXTENSIONCLASS_INCLUDEDIRS = ['include', 'src']

from util import getVersionForPackage
def getPackages(packages):
    """ Return a list of egg names together with their
        version specs according to the version-zopeX.cfg
        files.
    """
    result = list()
    for package in packages:
        if ' ' in package:
            package = package[:package.find(' ')]
        version = getVersionForPackage(package)
        result.append('%s==%s' % (package, version))
    return result


setup(name='Zope2',
      version = '2.12.0.a1',
      url='http://www.zope.org',
      license='ZPL 2.1',
      description='Zope2 application server / web framework',
      author='Zope Corporation and Contributors',
      author_email='zope-dev@zope.org',
      long_description=file("README.txt").read() + "\n" +
                       file(os.path.join("doc", "CHANGES.rst")).read(),

      packages=find_packages('src'),
      package_dir={'': 'src'},

      ext_modules=[

        # AccessControl
        Extension(
              name='AccessControl.cAccessControl',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=['src/AccessControl/cAccessControl.c'],
              depends=['include/ExtensionClass/ExtensionClass.h',
                       'include/ExtensionClass/pickle/pickle.c',
                       'include/Acquisition/Acquisition.h']),

        # DocumentTemplate
        Extension(
              name='DocumentTemplate.cDocumentTemplate',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=['src/DocumentTemplate/cDocumentTemplate.c']),

        Extension(
              name='MultiMapping._MultiMapping',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=["src/MultiMapping/_MultiMapping.c"],
              depends=["include/ExtensionClass/ExtensionClass.h"]),
        Extension(
              name='ThreadLock._ThreadLock',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=["src/ThreadLock/_ThreadLock.c"],
              depends=["include/ExtensionClass/ExtensionClass.h"]),
        Extension(
              name='Missing._Missing',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=["src/Missing/_Missing.c"],
              depends=["include/ExtensionClass/ExtensionClass.h"]),
        Extension(
              name='Record._Record',
              include_dirs=EXTENSIONCLASS_INCLUDEDIRS,
              sources=["src/Record/_Record.c"],
              depends=["include/ExtensionClass/ExtensionClass.h"]),

        # initgroups
        Extension(
              name='initgroups._initgroups',
              sources=['src/initgroups/_initgroups.c']),

        # indexes
        Extension(
              name='Products.PluginIndexes.TextIndex.Splitter.'
                   'ZopeSplitter.ZopeSplitter',
              sources=['src/Products/PluginIndexes/TextIndex/Splitter/'
                       'ZopeSplitter/src/ZopeSplitter.c']),
        Extension(
              name='Products.PluginIndexes.TextIndex.Splitter.'
                   'ISO_8859_1_Splitter.ISO_8859_1_Splitter',
              sources=['src/Products/PluginIndexes/TextIndex/Splitter/'
                       'ISO_8859_1_Splitter/src/ISO_8859_1_Splitter.c']),
        Extension(
              name='Products.PluginIndexes.TextIndex.Splitter.'
                   'UnicodeSplitter.UnicodeSplitter',
              sources=['src/Products/PluginIndexes/TextIndex/Splitter/'
                       'UnicodeSplitter/src/UnicodeSplitter.c']),
        Extension(
              name='Products.ZCTextIndex.stopper',
              sources=['src/Products/ZCTextIndex/stopper.c']),
        Extension(
              name='Products.ZCTextIndex.okascore',
              sources=['src/Products/ZCTextIndex/okascore.c']),

      ],

      install_requires=getPackages([
        'Acquisition',
        'DateTime',
        'docutils',
        'ExtensionClass',
        'Persistence',
        'pytz',
        'RestrictedPython',
        'tempstorage',
        'ZConfig',
        'zLOG',
        'zdaemon',
        'ZODB3',
        'zodbcode',
        'zope.component',
        'zope.configuration',
        'zope.container',
        'zope.contentprovider',
        'zope.contenttype',
        'zope.deferredimport',
        'zope.event',
        'zope.exceptions',
        'zope.formlib',
        'zope.i18n [zcml]',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.lifecycleevent',
        'zope.location',
        'zope.pagetemplate',
        'zope.proxy',
        'zope.publisher',
        'zope.schema',
        'zope.security',
        'zope.sendmail',
        'zope.sequencesort',
        'zope.site',
        'zope.size',
        'zope.structuredtext',
        'zope.tal',
        'zope.tales',
        'zope.testbrowser',
        'zope.testing',
        'zope.traversing',
        'zope.viewlet',
        'zope.app.component',
        'zope.app.container',
        'zope.app.form',
        'zope.app.locales',
        'zope.app.pagetemplate',
        'zope.app.publication',
        'zope.app.publisher',
        'zope.app.schema',
        'zope.app.testing',
      ]),

      extras_require = dict(
        zope_app = getPackages([
          'zope.annotation',
          'zope.cachedescriptors',
          'zope.copypastemove',
          'zope.datetime',
          'zope.decorator',
          'zope.deprecation',
          'zope.documenttemplate',
          'zope.dottedname',
          'zope.dublincore',
          'zope.error',
          'zope.filerepresentation',
          'zope.hookable',
          'zope.index',
          'zope.keyreference',
          'zope.minmax',
          'zope.modulealias',
          'zope.rdb',
          'zope.securitypolicy',
          'zope.server',
          'zope.session',
          'zope.thread',
          'zope.wfmc',
          'zope.app.annotation',
          'zope.app.apidoc',
          'zope.app.applicationcontrol',
          'zope.app.appsetup',
          'zope.app.authentication',
          'zope.app.basicskin',
          'zope.app.broken',
          'zope.app.cache',
          'zope.app.content',
          'zope.app.debug',
          'zope.app.dependable',
          'zope.app.error',
          'zope.app.exception',
          'zope.app.file',
          'zope.app.folder',
          'zope.app.generations',
          'zope.app.http',
          'zope.app.i18n',
          'zope.app.interface',
          'zope.app.intid',
          'zope.app.layers',
          'zope.app.onlinehelp',
          'zope.app.pluggableauth',
          'zope.app.preference',
          'zope.app.preview',
          'zope.app.principalannotation',
          'zope.app.renderer',
          'zope.app.rotterdam',
          'zope.app.security',
          'zope.app.securitypolicy',
          'zope.app.session',
          'zope.app.skins',
          'zope.app.sqlscript',
          'zope.app.traversing',
          'zope.app.tree',
          'zope.app.undo',
          'zope.app.wfmc',
          'zope.app.wsgi',
          'zope.app.xmlrpcintrospection',
          'zope.app.zapi',
          'zope.app.zcmlfiles',
          'zope.app.zopeappgenerations',
          'zope.app.zptpage',
          ]),
      ),

      include_package_data=True,
      zip_safe=False,
      entry_points={
         'console_scripts' : [
            'mkzeoinstance=Zope2.utilities.mkzeoinstance:main',
            'mkzopeinstance=Zope2.utilities.mkzopeinstance:main',
            'zpasswd=Zope2.utilities.zpasswd:main',
        ]
      },
      )
