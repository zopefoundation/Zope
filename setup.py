#! /usr/bin/env python
##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
'''Distutils setup file for Zope

Common usage: python setup.py build_ext --build-lib `pwd`/lib/python
'''

import os
import sys

from distutils.core import setup, run_setup
from distutils.extension import Extension


SETUP_BERKELEY = 0
SETUP_ZEO = 0
SETUP_OLD_BTREE = 1
SETUP_CACCESSCONTROL = 1
SETUP_DCPYEXPAT = 1
SETUP_SPLITTERS = 1


# a few constants
zope_corp = "Zope Corporation"
zodb_email = "zodb-dev@zope.org"
zodb_wiki = "http://www.zope.org/Wikis/ZODB/FrontPage"

top_dir = os.path.abspath(os.getcwd())
ec_root = os.path.join(top_dir, 'lib', 'Components', 'ExtensionClass')
ec_src = os.path.join(ec_root, 'src')
py_root = os.path.join(top_dir, 'lib', 'python')
ec_include = [ec_src]

# ExtensionClass
os.chdir(ec_root)
dist = run_setup('setup.py', script_args=sys.argv[1:], stop_after="run")
os.chdir(py_root)

# ZODB
cPersistence = Extension(name = 'ZODB.cPersistence',
                         include_dirs = ec_include,
                         sources= ['ZODB/cPersistence.c']
                         )

cPickleCache = Extension(name = 'ZODB.cPickleCache',
                         include_dirs = ec_include,
                         sources= ['ZODB/cPickleCache.c']
                         )

TimeStamp = Extension(name = 'ZODB.TimeStamp',
                      define_macros = [('USE_EXTENSION_CLASS', 1)],
                      include_dirs = ec_include,
                      sources= ['ZODB/TimeStamp.c']
                      )

coptimizations = Extension(name = 'ZODB.coptimizations',
                           include_dirs = ec_include,
                           sources= ['ZODB/coptimizations.c']
                           )

winlock = Extension(name = 'ZODB.winlock',
                    include_dirs = ec_include,
                    sources = ['ZODB/winlock.c']
                    )

setup(name="ZODB",
      version="3.1",
      description = "Z Object Database persistence system",
      author = zope_corp,
      author_email = zodb_email,
      url = zodb_wiki,

      packages=['ZODB', 'ZODB.tests'],
      
      ext_modules = [cPersistence, cPickleCache, TimeStamp,
                     coptimizations, winlock],
      headers = ["ZODB/cPersistence.h"]
      )


if SETUP_ZEO:
    setup(name = "ZEO", 
      version = "0.4.1",
      description = "Zope Enterprise Objects",
      author = zope_corp,
      author_email = zodb_email,
      url = zodb_wiki,

      packages = ['ZEO', 'ZEO.tests'],
      )


if SETUP_BERKELEY:
    # Berkeley storages
    setup(name="bsddb3Storage",
      description="ZODB storages based on Berkeley DB",
      author = zope_corp,
      author_email = zodb_email,
      url = zodb_wiki,
      package_dir = {'bsddb3Storage': 'bsddb3Storage/bsddb3Storage'},
      packages = ["bsddb3Storage", "bsddb3Storage.tests"],
      )


if SETUP_OLD_BTREE:
    old_btree_root = os.path.join(top_dir, 'lib', 'Components', 'BTree')
    old_btree_include = ec_include + ['ZODB']

    old_btree_modules = []
    for name in 'BTree', 'IIBTree', 'IOBTree', 'OIBTree', 'intSet':
        ext = Extension(name=name,
                        include_dirs=old_btree_include,
                        sources=[os.path.join(old_btree_root, '%s.c' % name)])
        old_btree_modules.append(ext)

    setup(name = "BTree",
          version = "?",
          description = "BTree package (for backward compatibility)",
          maintainer = "Zope Corporation",
          maintainer_email = "zope@zope.org",
          url = "http://www.zope.org",

          ext_modules = old_btree_modules,
          headers = [os.path.join(old_btree_root, "intSet.h")],
          )


# BTrees

btree_include = ec_include + ['ZODB']

oob = Extension(name = "BTrees._OOBTree",
                include_dirs = btree_include,
                sources = ['BTrees/_OOBTree.c'],
                )

oib = Extension(name = "BTrees._OIBTree",
                include_dirs = btree_include,
                sources = ['BTrees/_OIBTree.c'],
                )

iib = Extension(name = "BTrees._IIBTree",
                include_dirs = btree_include,
                sources = ['BTrees/_IIBTree.c'],
                define_macros = [('EXCLUDE_INTSET_SUPPORT', None)],
                )

iob = Extension(name = "BTrees._IOBTree",
                include_dirs = btree_include,
                sources = ['BTrees/_IOBTree.c'],
                define_macros = [('EXCLUDE_INTSET_SUPPORT', None)],
                )

fsb = Extension(name = "BTrees._fsBTree",
                include_dirs = btree_include,
                sources = ['BTrees/_fsBTree.c'],
                define_macros = [('EXCLUDE_INTSET_SUPPORT', None)],
                )

setup(name="BTrees",
      version="?",
      packages=["BTrees", "BTrees.tests"],
      ext_modules=[oob, oib, iib, iob, fsb],
      author=zope_corp,
      )


# DocumentTemplate

cdoctemp_ext = Extension(name = "DocumentTemplate.cDocumentTemplate",
                         include_dirs = ec_include,
                         sources = ['DocumentTemplate/cDocumentTemplate.c'],
                         )

setup(name="DocumentTemplate",
      version="?",
      packages=["DocumentTemplate", "DocumentTemplate.tests"],
      ext_modules=[cdoctemp_ext],
      author=zope_corp,
      )


# cAccessControl

if SETUP_CACCESSCONTROL:
    cactl_ext = Extension(name="AccessControl.cAccessControl",
                          include_dirs=ec_include,
                          sources=['AccessControl/cAccessControl.c'],
                          )

    setup(name="AccessControl",
          version="?",
          packages=["AccessControl", "AccessControl.tests"],
          ext_modules=[cactl_ext],
          author=zope_corp,
          )

# dcpyexpat

if SETUP_DCPYEXPAT:
    pyexpat_root = os.path.join(py_root, 'Shared', 'DC', 'xml', 'pyexpat')
    dcpyexpat_incl = [os.path.join(pyexpat_root, 'expat', 'xmlparse'),
                      os.path.join(pyexpat_root, 'expat', 'xmltok')]
    pfx = pyexpat_root + '/'

    dcpyexpat_ext = Extension(name='Shared.DC.xml.dcpyexpat',
                              include_dirs=dcpyexpat_incl,
                              define_macros = [('XML_NS',1)],
                              sources=[pfx + 'expat/xmlparse/xmlparse.c',
                                       pfx + 'expat/xmlparse/hashtable.c',
                                       pfx + 'expat/xmltok/xmlrole.c',
                                       pfx + 'expat/xmltok/xmltok.c',
                                       pfx + 'dcpyexpat.c',
                                       ]
                              )

    setup(name="dcpyexpat",
          version="?",
          packages=["Shared.DC.xml"],
          ext_modules=[dcpyexpat_ext],
          author=zope_corp,
          headers=[pfx + 'expat/xmlparse/xmlparse.h',
                   pfx + 'expat/xmlparse/hashtable.h',
                   pfx + 'expat/xmltok/nametab.h',
                   pfx + 'expat/xmltok/iasciitab.h',
                   pfx + 'expat/xmltok/xmltok.h',
                   pfx + 'expat/xmltok/asciitab.h',
                   pfx + 'expat/xmltok/xmldef.h',
                   pfx + 'expat/xmltok/xmltok_impl.h',
                   pfx + 'expat/xmltok/xmlrole.h',
                   pfx + 'expat/xmltok/utf8tab.h',
                   pfx + 'expat/xmltok/latin1tab.h',
                   ],
          )


# Splitter for ZCatalog
if SETUP_SPLITTERS:
    prefix1 = 'Products/PluginIndexes/TextIndex/Splitter/'
    prefix2 = prefix1.replace('/', '.')
    ext_modules = [
        Extension(prefix2 + "ZopeSplitter.ZopeSplitter",
                  [prefix1 + 'ZopeSplitter/src/ZopeSplitter.c']),
        Extension(prefix2 + "ISO_8859_1_Splitter.ISO_8859_1_Splitter",
                  [prefix1 + 'ISO_8859_1_Splitter/src/ISO_8859_1_Splitter.c']),
        Extension(prefix2 + "UnicodeSplitter.UnicodeSplitter",
                  [prefix1 + 'UnicodeSplitter/src/UnicodeSplitter.c']),
        ]

    setup(name="Splitter",
          version="1.0",
          description="Splitters for Zope 2.5",
          author="Andreas Jung",
          author_email="andreas@zope.com",
          url="http://www.zope.org/...",
          ext_modules=ext_modules,
          packages=['Products.PluginIndexes.TextIndex.Splitter']
          )


# Lib -- misc. support files
# This might be expanded with other Zope packages.
setup(name = "Other libraries",
      packages = ["Persistence",
                  "ThreadedAsync",
                  "zLOG", "zLOG.tests",
                  "zdaemon",
                  ]
      )

stopper = Extension(name = "Products.ZCTextIndex.stopper",
                    sources = ["Products/ZCTextIndex/stopper.c"])

setup(name = "Products.ZCTextIndex",
      ext_modules = [stopper])

os.chdir(top_dir)

