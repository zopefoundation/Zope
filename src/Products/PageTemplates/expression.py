"""``chameleon.tales`` expressions."""

import warnings
from ast import NodeTransformer
from ast import parse

from chameleon.astutil import Static
from chameleon.astutil import Symbol
from chameleon.codegen import template
from chameleon.tales import NotExpr
from chameleon.tales import StringExpr

from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.ZopeGuards import guarded_apply
from AccessControl.ZopeGuards import guarded_getattr
from AccessControl.ZopeGuards import guarded_getitem
from AccessControl.ZopeGuards import guarded_iter
from AccessControl.ZopeGuards import protected_inplacevar
from OFS.interfaces import ITraversable
from RestrictedPython import RestrictingNodeTransformer
from RestrictedPython.Utilities import utility_builtins
from z3c.pt import expressions
from zExceptions import NotFound
from zExceptions import Unauthorized
from zope.interface import implementer
from zope.tales.tales import ExpressionEngine
from zope.traversing.adapters import traversePathElement
from zope.traversing.interfaces import TraversalError

from .Expressions import render
from .interfaces import IZopeAwareEngine


_marker = object()

zope2_exceptions = (
    AttributeError,
    LookupError,
    NameError,
    TypeError,
    ValueError,
    NotFound,
    Unauthorized,
    TraversalError,
)


def static(obj):
    return Static(template("obj", obj=Symbol(obj), mode="eval"))


class BoboAwareZopeTraverse:
    traverse_method = 'restrictedTraverse'

    __slots__ = ()

    @classmethod
    def traverse(cls, base, request, path_items):
        """See ``zope.app.pagetemplate.engine``."""

        validate = getSecurityManager().validate
        path_items = list(path_items)
        path_items.reverse()

        while path_items:
            name = path_items.pop()

            if ITraversable.providedBy(base):
                base = getattr(base, cls.traverse_method)(name)
            else:
                found = traversePathElement(base, name, path_items,
                                            request=request)

                # If traverse_method is something other than
                # ``restrictedTraverse`` then traversal is assumed to be
                # unrestricted. This emulates ``unrestrictedTraverse``
                if cls.traverse_method != 'restrictedTraverse':
                    base = found
                    continue

                # Special backwards compatibility exception for the name ``_``,
                # which was often used for translation message factories.
                # Allow and continue traversal.
                if name == '_':
                    warnings.warn('Traversing to the name `_` is deprecated '
                                  'and will be removed in Zope 6.',
                                  DeprecationWarning)
                    base = found
                    continue

                # All other names starting with ``_`` are disallowed.
                # This emulates what restrictedTraverse does.
                if name.startswith('_'):
                    raise NotFound(name)

                # traversePathElement doesn't apply any Zope security policy,
                # so we validate access explicitly here.
                try:
                    validate(base, base, name, found)
                    base = found
                except Unauthorized:
                    # Convert Unauthorized to prevent information disclosures
                    raise NotFound(name)

        return base

    def __call__(self, base, econtext, call, path_items):
        request = econtext.get('request')

        if path_items:
            base = self.traverse(base, request, path_items)

        if call is False:
            return base

        if getattr(base, '__call__', _marker) is not _marker or \
           callable(base):
            base = render(base, econtext)

        return base


class TrustedBoboAwareZopeTraverse(BoboAwareZopeTraverse):
    traverse_method = 'unrestrictedTraverse'

    __slots__ = ()

    def __call__(self, base, econtext, call, path_items):
        request = econtext.get('request')

        base = self.traverse(base, request, path_items)

        if call is False:
            return base

        if getattr(base, '__call__', _marker) is not _marker or \
           isinstance(base, type):
            return base()

        return base


class PathExpr(expressions.PathExpr):
    exceptions = zope2_exceptions

    traverser = Static(template(
        "cls()", cls=Symbol(BoboAwareZopeTraverse), mode="eval"
    ))


class TrustedPathExpr(PathExpr):
    traverser = Static(template(
        "cls()", cls=Symbol(TrustedBoboAwareZopeTraverse), mode="eval"
    ))


class NocallExpr(expressions.NocallExpr, PathExpr):
    pass


class ExistsExpr(expressions.ExistsExpr):
    exceptions = zope2_exceptions


class RestrictionTransform(NodeTransformer):
    secured = {
        '_getattr_': guarded_getattr,
        '_getitem_': guarded_getitem,
        '_apply_': guarded_apply,
        '_getiter_': guarded_iter,
        '_inplacevar_': protected_inplacevar,
    }

    def visit_Name(self, node):
        value = self.secured.get(node.id)
        if value is not None:
            return Symbol(value)

        return node


class UntrustedPythonExpr(expressions.PythonExpr):
    restricted_python_transformer = RestrictingNodeTransformer()
    page_templates_expression_transformer = RestrictionTransform()

    # Make copy of parent expression builtins
    builtins = expressions.PythonExpr.builtins.copy()

    # Update builtins with Restricted Python utility builtins
    builtins.update({
        name: static(builtin) for (name, builtin) in utility_builtins.items()
    })

    def parse(self, string):
        encoded = string.encode('utf-8')
        node = parse(encoded, mode='eval')

        # Run Node Transformation from RestrictedPython:
        self.restricted_python_transformer.visit(node)

        # Run PageTemplate.expression RestrictedPython Transform:
        self.page_templates_expression_transformer.visit(node)

        return node


# Whether an engine is Zope aware does not depend on the class
# but how it is configured - especially, that is uses a Zope aware
# `PathExpr` implementation.
# Nevertheless, we mark the class as "Zope aware" for simplicity
# assuming that users of the class use a proper `PathExpr`
@implementer(IZopeAwareEngine)
class ChameleonEngine(ExpressionEngine):
    """Expression engine for ``chameleon.tales``.

    Only partially implemented: its ``compile`` is currently unusable
    """
    def compile(self, expression):
        raise NotImplementedError()


types = dict(
    python=UntrustedPythonExpr,
    string=StringExpr,
    not_=NotExpr,
    exists=ExistsExpr,
    path=PathExpr,
    provider=expressions.ProviderExpr,
    nocall=NocallExpr)


def createChameleonEngine(types=types, untrusted=True, **overrides):
    e = ChameleonEngine()

    def norm(k):
        return k[:-1] if k.endswith("_") else k

    e.untrusted = untrusted
    ts = e.types
    for k, v in types.items():
        k = norm(k)
        e.registerType(k, v)
    for k, v in overrides.items():
        k = norm(k)
        if k in ts:
            del ts[k]
        e.registerType(k, v)
    return e


def createTrustedChameleonEngine(**overrides):
    ovr = dict(python=expressions.PythonExpr, path=TrustedPathExpr)
    ovr.update(overrides)
    return createChameleonEngine(untrusted=False, **ovr)


_engine = createChameleonEngine()


def getEngine():
    return _engine


_trusted_engine = createTrustedChameleonEngine()


def getTrustedEngine():
    return _trusted_engine
