##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
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
    version='2.12.5',
    url='http://www.zope.org',
    license='ZPL 2.1',
    description='Zope2 application server / web framework',
    author='Zope Foundation and Contributors',
    author_email='zope-dev@zope.org',
    long_description=file("README.txt").read() + "\n" +
                     file(os.path.join("doc", "CHANGES.rst")).read(),

    packages=find_packages('src'),
    namespace_packages=['Products'],
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
            name='Products.ZCTextIndex.stopper',
            sources=['src/Products/ZCTextIndex/stopper.c']),
      Extension(
            name='Products.ZCTextIndex.okascore',
            sources=['src/Products/ZCTextIndex/okascore.c']),

    ],

    install_requires=[
      'Acquisition',
      'DateTime',
      'ExtensionClass',
      'Persistence',
      'RestrictedPython',
      'ZConfig',
      'ZODB3',
      'ZopeUndo',
      'docutils',
      'five.formlib',
      'pytz',
      'setuptools',
      'tempstorage',
      'transaction',
      'zdaemon',
      'zLOG',
      'zope.component',
      'zope.configuration',
      'zope.container',
      'zope.contentprovider',
      'zope.contenttype',
      'zope.deferredimport',
      'zope.event',
      'zope.exceptions',
      'zope.i18n [zcml]',
      'zope.i18nmessageid',
      'zope.interface',
      'zope.lifecycleevent',
      'zope.location',
      'zope.pagetemplate',
      'zope.processlifetime',
      'zope.proxy',
      'zope.publisher',
      'zope.schema',
      'zope.security',
      'zope.sendmail<3.7.0',
      'zope.sequencesort',
      'zope.site',
      'zope.size',
      'zope.structuredtext',
      'zope.tal',
      'zope.tales',
      'zope.testbrowser [zope-functional-testing]',
      'zope.testing',
      'zope.traversing',
      'zope.viewlet',
      'zope.app.publication',
      'zope.app.publisher',
      'zope.app.schema',
    ],

    include_package_data=True,
    zip_safe=False,
    entry_points={
       'console_scripts' : [
          'mkzeoinstance=Zope2.utilities.mkzeoinstance:main',
          'mkzopeinstance=Zope2.utilities.mkzopeinstance:main',
          'runzope=Zope2.Startup.run:run',
          'zopectl=Zope2.Startup.zopectl:run',
          'zpasswd=Zope2.utilities.zpasswd:main',
      ]
    },
)

setup(**params)
