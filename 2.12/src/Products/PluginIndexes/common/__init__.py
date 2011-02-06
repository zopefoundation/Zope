##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
#############################################################################

# This code is duplicated here from Products/ZCatalog/Catalog.py to avoid a
# unnecessary dependency on ZCatalog.
import types
try:
    from DocumentTemplate.cDocumentTemplate import safe_callable
except ImportError:
    def safe_callable(ob):
        # Works with ExtensionClasses and Acquisition.
        if hasattr(ob, '__class__'):
            if hasattr(ob, '__call__'):
                return 1
            else:
                return isinstance(ob, types.ClassType)
        else:
            return callable(ob)
