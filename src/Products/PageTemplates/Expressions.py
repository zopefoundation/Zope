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
"""Page Template Expression Engine

Page Template-specific implementation of TALES, with handlers
for Python expressions, string literals, and paths.
"""

import logging
import warnings

import OFS.interfaces
from AccessControl import safe_builtins
from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import aq_base
from MultiMapping import MultiMapping
from zExceptions import NotFound
from zExceptions import Unauthorized
from zope.component import queryUtility
from zope.contentprovider.tales import TALESProviderExpression
from zope.i18n import translate
from zope.interface import implementer
from zope.pagetemplate.engine import ZopeEngine as Z3Engine
from zope.proxy import removeAllProxies
from zope.tales.expressions import DeferExpr
from zope.tales.expressions import LazyExpr
from zope.tales.expressions import NotExpr
from zope.tales.expressions import PathExpr
from zope.tales.expressions import StringExpr
from zope.tales.expressions import SubPathExpr
from zope.tales.expressions import Undefs
from zope.tales.pythonexpr import PythonExpr
from zope.tales.tales import Context
from zope.tales.tales import ErrorInfo as BaseErrorInfo
from zope.tales.tales import Iterator
from zope.traversing.adapters import traversePathElement
from zope.traversing.interfaces import ITraversable

from . import ZRPythonExpr
from .interfaces import IUnicodeEncodingConflictResolver
from .interfaces import IZopeAwareEngine


SecureModuleImporter = ZRPythonExpr._SecureModuleImporter()

LOG = logging.getLogger('Expressions')

# In Zope 2 traversal semantics, NotFound or Unauthorized (the Zope 2
# versions) indicate that traversal has failed.  By default, zope.tales'
# engine doesn't recognize them as such which is why we extend its
# list here and make sure our implementation of the TALES
# Path Expression uses them
ZopeUndefs = Undefs + (NotFound, Unauthorized)


def boboAwareZopeTraverse(object, path_items, econtext):
    """Traverses a sequence of names, first trying attributes then items.

    This uses zope.traversing path traversal where possible and interacts
    correctly with objects providing OFS.interface.ITraversable when
    necessary (bobo-awareness).
    """
    request = getattr(econtext, 'request', None)
    validate = getSecurityManager().validate
    path_items = list(path_items)
    path_items.reverse()

    while path_items:
        name = path_items.pop()

        if OFS.interfaces.ITraversable.providedBy(object):
            object = object.restrictedTraverse(name)
        else:
            found = traversePathElement(object, name, path_items,
                                        request=request)

            # Special backwards compatibility exception for the name ``_``,
            # which was often used for translation message factories.
            # Allow and continue traversal.
            if name == '_':
                warnings.warn('Traversing to the name `_` is deprecated '
                              'and will be removed in Zope 6.',
                              DeprecationWarning)
                object = found
                continue

            # All other names starting with ``_`` are disallowed.
            # This emulates what restrictedTraverse does.
            if name.startswith('_'):
                raise NotFound(name)

            # traversePathElement doesn't apply any Zope security policy,
            # so we validate access explicitly here.
            try:
                validate(object, object, name, found)
                object = found
            except Unauthorized:
                # Convert Unauthorized to prevent information disclosures
                raise NotFound(name)

    return object


def trustedBoboAwareZopeTraverse(object, path_items, econtext):
    """Traverses a sequence of names, first trying attributes then items.

    This uses zope.traversing path traversal where possible and interacts
    correctly with objects providing OFS.interface.ITraversable when
    necessary (bobo-awareness).
    """
    request = getattr(econtext, 'request', None)
    path_items = list(path_items)
    path_items.reverse()

    while path_items:
        name = path_items.pop()
        if OFS.interfaces.ITraversable.providedBy(object):
            object = object.unrestrictedTraverse(name)
        else:
            object = traversePathElement(object, name, path_items,
                                         request=request)
    return object


def render(ob, ns):
    """Calls the object, possibly a document template, or just returns
    it if not callable.  (From DT_Util.py)
    """
    if hasattr(ob, '__render_with_namespace__'):
        ob = ZRPythonExpr.call_with_ns(ob.__render_with_namespace__, ns)
    else:
        # items might be acquisition wrapped
        base = aq_base(ob)
        # item might be proxied (e.g. modules might have a deprecation
        # proxy)
        base = removeAllProxies(base)
        if callable(base):
            try:
                if getattr(base, 'isDocTemp', 0):
                    ob = ZRPythonExpr.call_with_ns(ob, ns, 2)
                else:
                    ob = ob()
            except NotImplementedError:
                pass
    return ob


class _CombinedMapping:
    """Minimal auxiliary class to combine several mappings.

    Earlier mappings take precedence.
    """
    def __init__(self, *ms):
        self.mappings = ms

    def get(self, key, default):
        for m in self.mappings:
            value = m.get(key, self)
            if value is not self:
                return value
        return default


class UntrustedSubPathExpr(SubPathExpr):
    ALLOWED_BUILTINS = safe_builtins


class TrustedSubPathExpr(SubPathExpr):
    # we allow both Python's builtins (we are trusted)
    # as well as ``safe_builtins`` (because it may contain extensions)
    # Python's builtins take precedence, because those of
    # ``safe_builtins`` may have special restrictions for
    # the use in an untrusted context
    ALLOWED_BUILTINS = _CombinedMapping(
        __builtins__,
        safe_builtins)


class ZopePathExpr(PathExpr):

    _TRAVERSER = staticmethod(boboAwareZopeTraverse)
    SUBEXPR_FACTORY = UntrustedSubPathExpr

    def __init__(self, name, expr, engine):
        if not expr.strip():
            expr = 'nothing'
        super().__init__(name, expr, engine, self._TRAVERSER)

    # override this to support different call metrics (see bottom of
    # method) and Zope 2's traversal exceptions (ZopeUndefs instead of
    # Undefs)
    def _eval(self, econtext):
        for expr in self._subexprs[:-1]:
            # Try all but the last subexpression, skipping undefined ones.
            try:
                ob = expr(econtext)
            except ZopeUndefs:  # use Zope 2 expression types
                pass
            else:
                break
        else:
            # On the last subexpression allow exceptions through.
            ob = self._subexprs[-1](econtext)
            if self._hybrid:
                return ob

        if self._name == 'nocall':
            return ob

        # this is where we are different from our super class:
        return render(ob, econtext.vars)

    # override this to support Zope 2's traversal exceptions
    # (ZopeUndefs instead of Undefs)
    def _exists(self, econtext):
        for expr in self._subexprs:
            try:
                expr(econtext)
            except ZopeUndefs:  # use Zope 2 expression types
                pass
            else:
                return 1
        return 0


class TrustedZopePathExpr(ZopePathExpr):
    _TRAVERSER = staticmethod(trustedBoboAwareZopeTraverse)
    SUBEXPR_FACTORY = TrustedSubPathExpr


class SafeMapping(MultiMapping):
    """Mapping with security declarations and limited method exposure.

    Since it subclasses MultiMapping, this class can be used to wrap
    one or more mapping objects.  Restricted Python code will not be
    able to mutate the SafeMapping or the wrapped mappings, but will be
    able to read any value.
    """
    __allow_access_to_unprotected_subobjects__ = True
    push = pop = None

    _push = MultiMapping.push
    _pop = MultiMapping.pop


class ZopeContext(Context):

    def __init__(self, engine, contexts):
        super().__init__(engine, contexts)
        # wrap the top-level 'repeat' variable, as it is visible to
        # restricted code
        self.setContext('repeat', SafeMapping(self.repeat_vars))
        # regenerate the first scope and the scope stack after messing
        # with the global context
        self.vars = vars = contexts.copy()
        self._vars_stack = [vars]

    def translate(self, msgid, domain=None, mapping=None, default=None):
        context = self.contexts.get('request')
        return translate(
            msgid, domain=domain, mapping=mapping,
            context=context, default=default)

    def evaluateBoolean(self, expr):
        value = self.evaluate(expr)
        # here we override the normal zope.tales behaviour. zope.tales
        # doesn't care about the default in a boolean expression,
        # while we do (Zope 2 legacy, see the
        # BooleanAttributesAndDefault.html test case)
        if value is self.getDefault():
            return value
        return bool(value)

    def evaluateStructure(self, expr):
        """ customized version in order to get rid of unicode
            errors for all and ever
        """
        text = super().evaluateStructure(expr)
        return self._handleText(text, expr)

    def evaluateText(self, expr):
        """ customized version in order to get rid of unicode
            errors for all and ever
        """
        text = self.evaluate(expr)
        return self._handleText(text, expr)

    def _handleText(self, text, expr):

        if text is self.getDefault() or text is None:
            # XXX: should be unicode???
            return text

        if isinstance(text, str):
            # we love unicode, nothing to do
            return text

        elif isinstance(text, bytes):
            # bahh...non-unicode string..we need to convert it to unicode

            # catch ComponentLookupError in order to make tests shut-up.
            # This should not be a problem since it won't change the old
            # default behavior

            resolver = queryUtility(IUnicodeEncodingConflictResolver)
            if resolver is None:
                return text.decode('ascii')

            try:
                return resolver.resolve(
                    self.contexts.get('context'), text, expr)
            except UnicodeDecodeError as e:
                LOG.error("UnicodeDecodeError detected for expression \"%s\"\n"
                          "Resolver class: %s\n"
                          "Exception text: %s\n"
                          "Template: %s\n"
                          "Rendered text: %r" %
                          (expr, resolver.__class__, e,
                           self.contexts['template'].absolute_url(1), text))
                raise
        else:
            # This is a weird culprit ...calling text_type() on non-string
            # objects
            return str(text)

    def createErrorInfo(self, err, position):
        # Override, returning an object accessible to untrusted code.
        # See: https://bugs.launchpad.net/zope2/+bug/174705
        return ErrorInfo(err, position)

    def evaluateCode(self, lang, code):
        """ See ITALExpressionEngine.

        o This method is a fossil:  nobody actually calls it, but the
          interface requires it.
        """
        raise NotImplementedError


class ErrorInfo(BaseErrorInfo):
    """Information about an exception passed to an on-error handler.
    """
    __allow_access_to_unprotected_subobjects__ = True


# Whether an engine is Zope aware does not depend on the class
# but how it is configured - especially, that is uses a Zope aware
# `PathExpr` implementation.
# Nevertheless, we mark the class as "Zope aware" for simplicity
# assuming that users of the class use a proper `PathExpr`
@implementer(IZopeAwareEngine)
class ZopeEngine(Z3Engine):

    _create_context = ZopeContext


class ZopeIterator(Iterator):

    # allow iterator API to be accessed from (restricted) Python TALES
    # expressions
    __allow_access_to_unprotected_subobjects__ = True

    # The things below used to be attributes in
    # ZTUtils.Iterator.Iterator, however in zope.tales.tales.Iterator
    # they're methods.  We need BBB on the Python level so we redefine
    # them as properties here.  Eventually, we would like to get rid
    # of them, though, so that we won't have to maintain yet another
    # iterator class somewhere.

    @property
    def index(self):
        return super().index()

    @property
    def start(self):
        return super().start()

    @property
    def end(self):
        return super().end()

    @property
    def item(self):
        return super().item()

    # 'first' and 'last' are Zope 2 enhancements to the TALES iterator
    # spec.
    def first(self, name=None):
        if self.start:
            return True
        return not self.same_part(name, self._last_item, self.item)

    def last(self, name=None):
        if self.end:
            return True
        return not self.same_part(name, self.item, self._next)

    def same_part(self, name, ob1, ob2):
        if name is None:
            return ob1 == ob2
        no = object()
        return getattr(ob1, name, no) == getattr(ob2, name, no) is not no

    # 'first' needs to have access to the last item in the loop
    def __next__(self):
        if self._nextIndex > 0:
            self._last_item = self.item
        return super().__next__()

    def next(self):
        if self._nextIndex > 0:
            self._last_item = self.item
        return super().next()


@implementer(ITraversable)
class PathIterator(ZopeIterator):
    """A TALES Iterator with the ability to use first() and last() on
    subpaths of elements."""

    def traverse(self, name, furtherPath):
        if name in ('first', 'last'):
            method = getattr(self, name)
            # it's important that 'name' becomes a copy because we'll
            # clear out 'furtherPath'
            name = furtherPath[:]
            if not name:
                name = None
            # make sure that traversal ends here with us
            furtherPath[:] = []
            return method(name)
        return getattr(self, name)

    def same_part(self, name, ob1, ob2):
        if name is None:
            return ob1 == ob2
        if isinstance(name, str):
            name = name.split('/')
        elif isinstance(name, bytes):
            name = name.split(b'/')
        try:
            ob1 = boboAwareZopeTraverse(ob1, name, None)
            ob2 = boboAwareZopeTraverse(ob2, name, None)
        except ZopeUndefs:
            return False
        return ob1 == ob2


class UnicodeAwareStringExpr(StringExpr):

    def __call__(self, econtext):
        vvals = []
        if isinstance(self._expr, str):
            # coerce values through the Unicode Conflict Resolver
            evaluate = econtext.evaluateText
        else:
            evaluate = econtext.evaluate
        for var in self._vars:
            v = evaluate(var)
            vvals.append(v)
        return self._expr % tuple(vvals)


def createZopeEngine(zpe=ZopePathExpr, untrusted=True):
    e = ZopeEngine()
    e.iteratorFactory = PathIterator
    for pt in zpe._default_type_names:
        e.registerType(pt, zpe)
    e.registerType('string', UnicodeAwareStringExpr)
    e.registerType('python', ZRPythonExpr.PythonExpr)
    e.registerType('not', NotExpr)
    e.registerType('defer', DeferExpr)
    e.registerType('lazy', LazyExpr)
    e.registerType('provider', TALESProviderExpression)
    e.registerBaseName('modules', SecureModuleImporter)
    e.untrusted = untrusted
    return e


def createTrustedZopeEngine():
    # same as createZopeEngine, but use non-restricted Python
    # expression evaluator
    # still uses the ``SecureModuleImporter``
    e = createZopeEngine(TrustedZopePathExpr, untrusted=False)
    e.types['python'] = PythonExpr
    return e


_engine = createZopeEngine()


def getEngine():
    return _engine


_trusted_engine = createTrustedZopeEngine()


def getTrustedEngine():
    return _trusted_engine
