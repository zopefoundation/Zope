##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
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
"""Use structured monkey-patching to enable ``ISized`` adapters for
Zope 2 objects.
"""

from Products.Five import fivemethod
from Products.Five import isFiveMethod
from zope.size.interfaces import ISized
from zope.testing.cleanup import addCleanUp  # NOQA


# holds classes that were monkeyed with; for clean up
_monkied = []


@fivemethod
def get_size(self):
    size = ISized(self, None)
    if size is not None:
        unit, amount = size.sizeForSorting()
        if unit == 'byte':
            return amount
    method = getattr(self, '__five_original_get_size', None)
    if method is not None:
        return self.__five_original_get_size()


def classSizable(class_):
    """Monkey the class to be sizable through Five"""
    # tuck away the original method if necessary
    if hasattr(class_, "get_size") and not isFiveMethod(class_.get_size):
        class_.__five_original_get_size = class_.get_size
    class_.get_size = get_size
    # remember class for clean up
    _monkied.append(class_)


def sizable(_context, class_):
    _context.action(
        discriminator=('five:sizable', class_),
        callable=classSizable,
        args=(class_,)
    )


def killMonkey(class_, name, fallback, attr=None):
    """Die monkey, die!"""
    method = getattr(class_, name, None)
    if isFiveMethod(method):
        original = getattr(class_, fallback, None)
        if original is not None:
            delattr(class_, fallback)
        if original is None or isFiveMethod(original):
            try:
                delattr(class_, name)
            except AttributeError:
                pass
        else:
            setattr(class_, name, original)

    if attr is not None:
        try:
            delattr(class_, attr)
        except (AttributeError, KeyError):
            pass


def unsizable(class_):
    """Restore class's initial state with respect to being sizable"""
    killMonkey(class_, 'get_size', '__five_original_get_size')


def cleanUp():
    for class_ in _monkied:
        unsizable(class_)


addCleanUp(cleanUp)
del addCleanUp
