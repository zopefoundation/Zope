##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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

from distutils.core import setup, Extension
setup(name="_ThreadLock", version="2.0",
      ext_modules=[
         Extension("_ThreadLock", ["_ThreadLock.c"],
                   include_dirs = ['.', '../ExtensionClass'],
                   depends = ['../ExtensionClass/ExtensionClass.h']),
         ])

