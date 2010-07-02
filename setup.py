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
from setuptools import setup, find_packages


setup(name='Zope2',
    version='2.13.0a2.dev',
    url='http://zope2.zope.org',
    license='ZPL 2.1',
    description='Zope2 application server / web framework',
    author='Zope Foundation and Contributors',
    author_email='zope-dev@zope.org',
    long_description=file("README.txt").read() + "\n" +
                     file(os.path.join("doc", "CHANGES.rst")).read(),

    packages=find_packages('src'),
    namespace_packages=['Products'],
    package_dir={'': 'src'},
    install_requires=[
      'AccessControl',
      'Acquisition',
      'DateTime',
      'DocumentTemplate',
      'ExtensionClass',
      'Missing',
      'MultiMapping',
      'Persistence',
      'Products.ZCTextIndex',
      'Record',
      'RestrictedPython',
      'ZConfig',
      'ZODB3',
      'ZopeUndo',
      'docutils',
      'initgroups',
      'nt_svcutils',
      'pytz',
      'setuptools',
      'tempstorage',
      'transaction',
      'zdaemon',
      'zExceptions',
      'zope.browser',
      'zope.browsermenu',
      'zope.browserpage',
      'zope.browserresource',
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
      'zope.ptresource',
      'zope.publisher',
      'zope.schema',
      'zope.security',
      'zope.sendmail',
      'zope.sequencesort',
      'zope.site',
      'zope.size',
      'zope.structuredtext',
      'zope.tal',
      'zope.tales >= 3.5.0',
      'zope.testbrowser',
      'zope.testing',
      'zope.traversing',
      'zope.viewlet',
    ],

    include_package_data=True,
    zip_safe=False,
    entry_points={
       'paste.app_factory': [
          'main=Zope2.Startup.run:make_wsgi_app',
       ],
       'console_scripts': [
          'mkzopeinstance=Zope2.utilities.mkzopeinstance:main',
          'runzope=Zope2.Startup.run:run',
          'zopectl=Zope2.Startup.zopectl:run',
          'zpasswd=Zope2.utilities.zpasswd:main',
          # 'addzope2user=Zope2.utilities.adduser:main'
      ],
    },
)
