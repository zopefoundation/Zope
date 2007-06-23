##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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

"""Datatypes for warning filter component """

def warn_category(category):
    import re, types
    if not category:
        return Warning
    if re.match("^[a-zA-Z0-9_]+$", category):
        try:
            cat = eval(category)
        except NameError:
            raise ValueError("unknown warning category: %s" % `category`)
    else:
        i = category.rfind(".")
        module = category[:i]
        klass = category[i+1:]
        try:
            m = __import__(module, None, None, [klass])
        except ImportError:
            raise ValueError("invalid module name: %s" % `module`)
        try:
            cat = getattr(m, klass)
        except AttributeError:
            raise ValueError("unknown warning category: %s" % `category`)
    if (not isinstance(cat, types.ClassType) or
        not issubclass(cat, Warning)):
        raise ValueError("invalid warning category: %s" % `category`)
    return cat


def warn_action(val):
    OK = ("error", "ignore", "always", "default", "module", "once")
    if val not in OK:
        raise ValueError, "warning action %s not one of %s" % (val, OK)
    return val

def warning_filter_handler(section):
    import warnings
    # add the warning filter
    warnings.filterwarnings(section.action, section.message, section.category,
                            section.module, section.lineno, 1)
    return section
