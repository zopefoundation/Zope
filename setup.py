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

from setuptools import find_packages
from setuptools import setup


HERE = os.path.abspath(os.path.dirname(__file__))


def _read_file(filename):
    with open(os.path.join(HERE, filename)) as f:
        return f.read()


README = _read_file('README.rst')
CHANGES = _read_file('CHANGES.rst')

version = '4.5.5'


setup(
    name='Zope',
    version=version,
    url='https://zope.readthedocs.io/en/latest/',
    project_urls={
        'Documentation': 'https://zope.readthedocs.io',
        'Issue Tracker': 'https://github.com/zopefoundation/Zope/issues',
        'Sources': 'https://github.com/zopefoundation/Zope',
    },
    license='ZPL 2.1',
    description='Zope application server / web framework',
    author='Zope Foundation and Contributors',
    author_email='zope-dev@zope.org',
    long_description="\n\n".join([README, CHANGES]),
    classifiers=[
        'Development Status :: 6 - Mature',
        "Environment :: Web Environment",
        "Framework :: Zope :: 4",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    packages=find_packages('src'),
    namespace_packages=['Products', 'Shared', 'Shared.DC', 'zmi'],
    package_dir={'': 'src'},
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,<3.9',
    install_requires=[
        'AccessControl >= 4.2',
        'Acquisition',
        'BTrees',
        'Chameleon >= 3.7.0',
        'DateTime',
        'DocumentTemplate >=3.0, <4.0',
        'ExtensionClass',
        'MultiMapping',
        'PasteDeploy',
        'Persistence',
        'RestrictedPython',
        'ZConfig >= 2.9.2',
        'ZODB',
        'ipaddress ; python_version=="2.7"',
        'setuptools >= 36.2',
        'six',
        'transaction >= 2.4',
        'waitress',
        'zExceptions >= 3.4',
        'z3c.pt',
        'zope.browser',
        'zope.browsermenu',
        'zope.browserpage >= 4.4.0.dev0',
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
        'zope.tales >= 5.0.2',
        'zope.testbrowser',
        'zope.testing',
        'zope.traversing',
        'zope.viewlet',
    ],
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'docs': [
            'Sphinx',
            'sphinx_rtd_theme',
            'repoze.sphinx.autointerface',
            'tempstorage',
        ],
        'wsgi': [
            'Paste',
        ],
    },
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
            'zconsole=Zope2.utilities.zconsole:main',
        ],
        'zodbupdate.decode': [
            'decodes = OFS:zodbupdate_decode_dict',
        ],
        'zodbupdate': [
            'renames = OFS:zodbupdate_rename_dict',
        ],
    },
)
