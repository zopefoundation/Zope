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

import os
from setuptools import setup, find_packages, Extension

setup(name='Zope2',
    version='2.12.23',
    url='http://www.zope.org',
    license='ZPL 2.1',
    description='Zope2 application server / web framework',
    author='Zope Foundation and Contributors',
    author_email='zope-dev@zope.org',
    long_description=file("README.txt").read() + "\n" +
                     file(os.path.join("doc", "CHANGES.rst")).read(),

    packages=find_packages('src'),
    namespace_packages=['Products', 'Shared', 'Shared.DC'],
    package_dir={'': 'src'},

    ext_modules=[

      # AccessControl
      Extension(
            name='AccessControl.cAccessControl',
            include_dirs=['include', 'src'],
            sources=['src/AccessControl/cAccessControl.c'],
            depends=['include/ExtensionClass/ExtensionClass.h',
                     'include/Acquisition/Acquisition.h']),

      # DocumentTemplate
      Extension(
            name='DocumentTemplate.cDocumentTemplate',
            include_dirs=['include', 'src'],
            sources=['src/DocumentTemplate/cDocumentTemplate.c'],
            depends=['include/ExtensionClass/ExtensionClass.h']),

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
      'Missing',
      'MultiMapping',
      'Persistence',
      'Products.ZSQLMethods',
      'Record',
      'RestrictedPython',
      'ThreadLock',
      'ZConfig',
      'ZODB3',
      'ZopeUndo',
      'docutils',
      'five.formlib',
      'initgroups',
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
      'zope.mkzeoinstance',
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
       'console_scripts': [
          'mkzeoinstance=zope.mkzeoinstance:main',
          'mkzopeinstance=Zope2.utilities.mkzopeinstance:main',
          'runzope=Zope2.Startup.run:run',
          'zopectl=Zope2.Startup.zopectl:run',
          'zpasswd=Zope2.utilities.zpasswd:main',
      ],
    },
)
