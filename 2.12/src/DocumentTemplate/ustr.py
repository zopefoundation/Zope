##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ustr function.

$Id$
"""

nasty_exception_str = getattr(Exception.__str__, 'im_func', None)

def ustr(v):
    """Convert any object to a plain string or unicode string,
    minimising the chance of raising a UnicodeError. This
    even works with uncooperative objects like Exceptions
    """
    if isinstance(v, basestring):
        return v
    else:
        fn = getattr(v,'__str__',None)
        if fn is not None:
            # An object that wants to present its own string representation,
            # but we dont know what type of string. We cant use any built-in
            # function like str() or unicode() to retrieve it because
            # they all constrain the type which potentially raises an exception.
            # To avoid exceptions we have to call __str__ direct.
            if getattr(fn,'im_func',None)==nasty_exception_str:
                # Exception objects have been optimised into C, and their
                # __str__ function fails when given a unicode object.
                # Unfortunately this scenario is all too common when
                # migrating to unicode, because of code which does:
                # raise ValueError(something_I_wasnt_expecting_to_be_unicode)
                return _exception_str(v)
            else:
                # Trust the object to do this right
                v = fn()
                if isinstance(v, basestring):
                    return v
                else:
                    raise ValueError('__str__ returned wrong type')
        # Drop through for non-instance types, and instances that
        # do not define a special __str__
        return str(v)


def _exception_str(exc):
    if hasattr(exc, 'args'):
        if not exc.args:
            return ''
        elif len(exc.args) == 1:
            return ustr(exc.args[0])
        else:
            return str(exc.args)
    return str(exc)
