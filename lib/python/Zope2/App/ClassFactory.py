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
"""Zope Framework Class Finder
"""
import OFS.Uninstalled

def ClassFactory(jar, module, name,
                  _silly=('__doc__',), _globals={},
                  ):
    try:
        if module[:1]=='*':
            # ZCLass! Yee ha!
            return jar.root()['ZGlobals'][module]
        else:
            m=__import__(module, _globals, _globals, _silly)

        return getattr(m, name)
    except:
        return OFS.Uninstalled.Broken(jar, None, (module, name))
