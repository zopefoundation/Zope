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
##############################################################################
"""Commonly used utility functions."""

import os
import sys

from Acquisition import aq_base
from Acquisition import aq_parent
from zope.deferredimport import deprecated


deprecated(
    'Please import from zope.datetime.'
    ' This backwards compatibility import will go away in Zope 6.',
    weekday_abbr='zope.datetime:weekday_abbr',
    weekday_full='zope.datetime:weekday_full',
    monthname='zope.datetime:monthname',
    iso8601_date='zope.datetime:iso8601_date',
    rfc850_date='zope.datetime:rfc850_date',
    rfc1123_date='zope.datetime:rfc1123_date',
)

deprecated(
    'Please import from os.path.'
    ' This backwards compatibility import will go away in Zope 6.',
    realpath='os.path:realpath',
)

deprecated(
    'Please import time directly.'
    ' This backwards compatibility import will go away in Zope 6.',
    time='time',
)


attrget = getattr


def absattr(attr, callable=callable):
    # Return the absolute value of an attribute,
    # calling the attr if it is callable.
    if callable(attr):
        return attr()
    return attr


def is_acquired(ob, hasattr=hasattr, aq_base=aq_base, absattr=absattr):
    # Return true if this object is not considered to be
    # a direct subobject of its acquisition parent
    # Note that this method is misnamed since parents can (and do)
    # spoof it. It is not a true measure of whether something is
    # acquired, it relies on the parent's parent-ness exclusively
    import warnings
    warnings.warn(
        "The function `is_acquired` is deprecated "
        "and will be removed in Zope 6.",
        DeprecationWarning)
    if not hasattr(ob, '__parent__'):
        # We can't be acquired if we don't have an __parent__
        return 0

    parent = aq_base(aq_parent(ob))
    absId = absattr(ob.id)

    if hasattr(parent, absId):
        # Consider direct attributes not acquired
        return 0

    if hasattr(parent, '__getitem__'):
        # Use __getitem__ as opposed to has_key to avoid TTW namespace
        # issues, and to support the most minimal mapping objects
        try:
            # We assume that getitem will not acquire which
            # is the standard behavior for Zope objects
            if aq_base(aq_parent(ob)[absId]) is aq_base(ob):
                # This object is an item of the aq_parent, its not acquired
                return 0
        except KeyError:
            pass

    if hasattr(aq_base(ob), 'isTopLevelPrincipiaApplicationObject') and \
            ob.isTopLevelPrincipiaApplicationObject:
        # This object the top level
        return 0
    return 1  # This object is acquired by our measure


def package_home(globals_dict):
    __name__ = globals_dict['__name__']
    m = sys.modules[__name__]
    if hasattr(m, '__path__'):
        r = m.__path__[0]
    elif "." in __name__:
        r = sys.modules[__name__[:__name__.rfind('.')]].__path__[0]
    else:
        r = __name__
    return os.path.abspath(r)


def Dictionary(**kw):
    import warnings
    warnings.warn(
        "The function `Dictionary` is deprecated "
        "and will be removed in Zope 6.",
        DeprecationWarning)
    return kw  # Sorry Guido
