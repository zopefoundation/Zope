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

params = dict(name='Zope2',
    version='2.12.0a3',
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

    install_requires=[
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
    ],

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

setup(**params)
