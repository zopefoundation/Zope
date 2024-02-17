##############################################################################
#
# Copyright (c) 2002-2024 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from functools import wraps
from inspect import signature


class Retry(Exception):
    """Raise this to retry a request
    """

    def __init__(self, t=None, v=None, tb=None):
        self._args = t, v, tb

    def reraise(self):
        t, v, tb = self._args
        if t is None:
            t = Retry
        if tb is None:
            raise t(v)
        try:
            raise v.with_traceback(tb)
        finally:
            tb = None


_ZPUBLISH_ATTR = "__zpublishable__"


def zpublish(publish=True, callable=None):
    """decorator signaling design for/not for publication.

    Usage:

      @zpublish
      def f(...): ...

      @zpublish(True)
      def f(...): ...

        ``f`` is designed to be published by ``ZPublisher``.

      @zpublish(False)
      def f(...): ...
        ``ZPublisher`` should not publish ``f``

      @zpublish...
      class C: ...
        instances of ``C`` can/can not be published by ``ZPublisher``.

      zpublish(publish=..., callable=obj)
        returns a wrapper for callable *obj* with the same signature;
        *publish* determines its publishability.

    ``Zpublish(f)`` is equivalent to ``zpublish(True)(f)`` if
    ``f`` is not a boolean.
    """
    if callable is not None:
        assert isinstance(publish, bool), "publish must be a boolean"

        @zpublish(publish)
        @wraps(callable)
        def wrapper(*args, **kw):
            return callable(*args, **kw)
        wrapper.__signature__ = signature(callable, follow_wrapped=False)
        return wrapper

    if not isinstance(publish, bool):
        return zpublish(True)(publish)

    def wrap(f):
        setattr(f, _ZPUBLISH_ATTR, publish)
        return f

    return wrap
