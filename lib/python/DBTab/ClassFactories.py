##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Available ZODB class factories.

$Id$"""

import OFS.Uninstalled


class_factories = {}

def minimalClassFactory(jar, module, name,
                        _silly=('__doc__',), _globals={},
                        ):
    """Minimal class factory.

    If any class is not found, this class factory will propagate
    the exception to the application, unlike the other class factories.
    """
    m = __import__(module, _globals, _globals, _silly)
    return getattr(m, name)

class_factories['minimal'] = minimalClassFactory



def simpleClassFactory(jar, module, name,
                       _silly=('__doc__',), _globals={},
                       ):
    """Class factory without ZClass support.
    """
    try:
        m = __import__(module, _globals, _globals, _silly)
        return getattr(m, name)
    except:
        return OFS.Uninstalled.Broken(jar, None, (module, name))

class_factories['simple'] = simpleClassFactory



def zopeClassFactory(jar, module, name,
                     _silly=('__doc__',), _globals={},
                     ):
    """Class factory with ZClass support.
    """
    try:
        if module[:1]=='*':
            # ZCLass! Yee ha!
            return jar.root()['ZGlobals'][module]
        else:
            m=__import__(module, _globals, _globals, _silly)

        return getattr(m, name)
    except:
        return OFS.Uninstalled.Broken(jar, None, (module, name))

class_factories['zope'] = zopeClassFactory



def autoClassFactory(jar, module, name):
    """Class factory with ZClasses and support for central class definitions.
    """
    # If not the root connection, use the class factory from
    # the root database, otherwise use the Zope class factory.
    root_conn = getattr(jar, '_root_connection', None)
    root_db = getattr(root_conn, '_db', None)
    if root_db is not None:
        return root_db.classFactory(root_conn, module, name)
    else:
        return zopeClassFactory(jar, module, name)

class_factories['auto'] = autoClassFactory

