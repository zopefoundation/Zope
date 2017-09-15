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

HERE = os.path.abspath(os.path.dirname(__file__))


def _read_file(filename):
    with open(os.path.join(HERE, filename)) as f:
        return f.read()


README = _read_file('README.rst')
CHANGES = _read_file('CHANGES.rst')

version = '4.0b1'

setup(
    name='Zope',
    version=version,
    url='https://zope.readthedocs.io/en/latest/',
    license='ZPL 2.1',
    description='Zope application server / web framework',
    author='Zope Foundation and Contributors',
    author_email='zope-dev@zope.org',
    long_description="\n\n".join([README, CHANGES]),
    classifiers=[
        'Development Status :: 6 - Mature',
        "Environment :: Web Environment",
        "Framework :: Zope2",
        "License :: OSI Approved :: Zope Public License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    packages=find_packages('src'),
    namespace_packages=['Products', 'Shared', 'Shared.DC'],
    package_dir={'': 'src'},
    install_requires=[
        'AccessControl >= 4.0a8.dev0',
        'Acquisition',
        'BTrees',
        'DateTime',
        'DocumentTemplate',
        'ExtensionClass',
        'MultiMapping',
        'PasteDeploy',
        'Persistence',
        'RestrictedPython',
        'ZConfig >= 2.9.2',
        'ZODB',
        'setuptools',
        'six',
        'transaction',
        'waitress',
        'zExceptions >= 3.4',
        'z3c.pt',
        'zope.browser',
        'zope.browsermenu',
        'zope.browserpage >= 4.0',
        'zope.browserresource >= 3.11',
        'zope.component',
        'zope.configuration',
        'zope.container',
        'zope.contentprovider',
        'zope.contenttype',
        'zope.deferredimport',
        'zope.event',
        'zope.exceptions',
        'zope.globalrequest',
        'zope.i18n [zcml]',
        'zope.i18nmessageid',
        'zope.interface >= 3.8',
        'zope.lifecycleevent',
        'zope.location',
        'zope.pagetemplate >= 4.0.2',
        'zope.processlifetime',
        'zope.proxy',
        'zope.ptresource',
        'zope.publisher',
        'zope.schema',
        'zope.security',
        'zope.sequencesort',
        'zope.site',
        'zope.size',
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
        'paste.filter_app_factory': [
            'httpexceptions=ZPublisher.httpexceptions:main',
        ],
        'console_scripts': [
            'addzope2user=Zope2.utilities.adduser:main',
            'runwsgi=Zope2.Startup.serve:main',
            'mkwsgiinstance=Zope2.utilities.mkwsgiinstance:main',
        ],
    },
)
