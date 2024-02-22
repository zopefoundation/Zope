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
from inspect import Parameter
from inspect import Signature
from inspect import signature
from itertools import chain
from types import FunctionType


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


def zpublish(publish=True, *, methods=None):
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

      @zpublish(methods="METHOD")
      def f(...):
          ``ZPublisher`` should publish ``f`` for request method *METHOD*

      zpublish(methods=("M1", "M2", ...))
      def f(...):
          ``ZPublisher`` should publish ``f`` for all
          request methods mentioned in *methods*.


      @zpublish...
      class C: ...
        instances of ``C`` can/can not be published by ``ZPublisher``.


    ``zpublish(f)`` is equivalent to ``zpublish(True)(f)`` if
    ``f`` is not a boolean.
    """
    if not isinstance(publish, bool):
        return zpublish(True)(publish)

    if methods is not None:
        assert publish
        publish = ((methods.upper(),) if isinstance(methods, str)
                   else tuple(m.upper() for m in methods) if methods
                   else False)

    def wrap(f):
        # *publish* is either ``True``, ``False`` or a tuple
        # of allowed request methods
        setattr(f, _ZPUBLISH_ATTR, publish)
        return f

    return wrap


def zpublish_mark(obj, default=None):
    """the publication indication effective at *obj* or *default*.

    For an instance, the indication usually comes from its class
    or a base class; a function/method typically carries the
    indication itself.

    The publication indication is either ``True`` (publication allowed),
    ``False`` (publication disallowed) or a tuple
    of request method names for which publication is allowed.
    """
    return getattr(obj, _ZPUBLISH_ATTR, default)


def zpublish_marked(obj):
    """true if a publication indication is effective at *obj*."""
    return zpublish_mark(obj) is not None


def zpublish_wrap(callable, *, conditional=True, publish=True, methods=None):
    """wrap *callable* to provide a publication indication.

    Return *callable* unchanged if *conditional* and a publication indication
    is already effective at *callable*;
    otherwise, return a signature preserving wrapper
    with publication control given by *publish* and *methods*.
    """
    if conditional and zpublish_marked(callable):
        return callable

    @zpublish(publish, methods=methods)
    @wraps(callable)
    def wrapper(*args, **kw):
        return callable(*args, **kw)
    # Signature preservation is particularly important for ``mapply``.
    # It allows an instance to specify the signature to be used for
    # its ``__call__`` method via attributes ``__code__`` and
    # ``__defaults__``.
    # We must respect such specifications
    cls = callable.__class__
    if isinstance(getattr(cls, "__call__", None), FunctionType) \
       and getattr(callable, "__code__", cls) is not cls \
       and getattr(callable, "__defaults__", cls) is not cls:
        # Signature specification via ``__code__`` and ``__defaults__``.
        code = callable.__code__
        varnames = code.co_varnames
        argcount = code.co_argcount
        defaults = callable.__defaults__ or ()
        pos = argcount - len(defaults)
        sig = Signature(tuple(
            Parameter(z[0], Parameter.POSITIONAL_OR_KEYWORD, default=z[1])
            for z in chain(
                ((n, Parameter.empty) for n in varnames[:pos]),
                zip(varnames[pos:], defaults))))
    else:
        sig = signature(callable)
    wrapper.__signature__ = sig
    return wrapper
