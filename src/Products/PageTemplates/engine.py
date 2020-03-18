"""``chameleon`` integration.

We use the ``zope.tales`` expression implementation (as adapted for ``Zope``)
not that of ``chemeleon.tales``.
"""

import ast
import copy
import logging
import re
import uuid
import weakref

from chameleon.astutil import Static
from chameleon.astutil import Symbol
from chameleon.codegen import template
from chameleon.tal import RepeatDict
from chameleon.zpt.template import Macros

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from MultiMapping import MultiMapping
from Products.PageTemplates.Expressions import getEngine
from z3c.pt.pagetemplate import PageTemplate as ChameleonPageTemplate
from zope.interface import implementer
from zope.interface import provider
from zope.pagetemplate.interfaces import IPageTemplateEngine
from zope.pagetemplate.interfaces import IPageTemplateProgram


# Declare Chameleon's repeat dictionary public but prevent modifications
#  by untrusted code
RepeatDict.security = ClassSecurityInfo()
RepeatDict.security.declareObjectPublic()
RepeatDict.security.declarePrivate(  # NOQA: D001
    *(set(dir(RepeatDict)) - set(dir(MultiMapping))))  # NOQA: D001
RepeatDict.__allow_access_to_unprotected_subobjects__ = True
InitializeClass(RepeatDict)

# Declare Chameleon Macros object accessible
# This makes subscripting work, as in template.macros['name']
Macros.__allow_access_to_unprotected_subobjects__ = True

re_match_pi = re.compile(r'<\?python([^\w].*?)\?>', re.DOTALL)
logger = logging.getLogger('Products.PageTemplates')


# zt_expr registry management
#  ``chameleon`` compiles TALES expressions to Python byte code
#  which has no support for arbitrary Python expressions but
#  can handle global (called `Static`) objects which include
#  globally defined functions.
#  We must pass ``MappedExpr`` instances to the ``zope`` TALES
#  expressions. We use a zt_expr registry accessed via the global
#  function ``_fetch_zt_expr``.

_zt_expr_registry = {}


def _fetch_zt_expr(eid):
    return _zt_expr_registry[eid]


_fetch_zt_expr_node = Static(Symbol(_fetch_zt_expr))


def _del_zt_expr(ref):
    try:
        del _zt_expr_registry[ref.eid]
    except KeyError:
        pass


def _c_context_2_z_context(c_context):
    z_context = copy.copy(c_context["__zt_context__"])
    # not sure that ``lazy`` works as expected
    z_context.vars = dict(c_context.vars)
    return z_context


_c_context_2_z_context_node = Static(Symbol(_c_context_2_z_context))


class LifetimeRef(weakref.ref):
    atexit = False

    def __init__(self, obj, callback, eid):
        self.eid = eid
        super(LifetimeRef, self).__init__(obj, callback)


class MappedExpr(object):
    """map expression: ``zope.tales`` --> ``chameleon.tales``."""
    def __init__(self, z_expr, lifetime_ref):
        eid = self.eid = uuid.uuid4().int
        z_expr.lifetime_ref = \
            LifetimeRef(lifetime_ref(), _del_zt_expr, eid=eid)
        _zt_expr_registry[eid] = z_expr

    def __call__(self, target, c_engine):
        return template(
            "target = fetch_zt_expr(eid)(c2z_context(econtext))",
            target=target,
            fetch_zt_expr=_fetch_zt_expr_node,
            eid=ast.Num(self.eid),
            c2z_context=_c_context_2_z_context_node)


class MappedExprType(object):
    """map expression type: ``zope.tales`` --> ``chameleon.tales``."""
    def __init__(self, type, handler, engine, lifetime_ref):
        self.type = type
        self.handler = handler
        self.engine = engine
        self.lifetime_ref = lifetime_ref

    def __call__(self, expression):
        return MappedExpr(self.handler(self.type, expression, self.engine),
                          self.lifetime_ref)


class Lifetime(object):
    """Auxiliary class to clean up resources when a template is deleted."""


class ChPageTemplate(ChameleonPageTemplate):
    """override to get an integrated default marker."""
    def _compile(self, body, builtins):
        code = super(ChPageTemplate, self)._compile(body, builtins)
        # redefine ``__default`` as ``zope.tales.tales._default``
        #  Potentially this could be simpler
        frags = code.split("\n", 5)
        for i, frag in enumerate(frags[:-1]):
            if frag.startswith("__default = "):
                frags[i] = "from zope.tales.tales import _default as __default"
                break
        else:
            raise RuntimeError("unexpected code prelude %s" % frags[:-1])
        return "\n".join(frags)


@implementer(IPageTemplateProgram)
@provider(IPageTemplateEngine)
class Program(object):

    def __init__(self, template, lifetime):
        self.template = template
        self.lifetime = lifetime

    def __call__(self, context, macros, tal=True, **options):
        if tal is False:
            return self.template.body

        # Swap out repeat dictionary for Chameleon implementation
        # and store wrapped dictionary in new variable -- this is
        # in turn used by the secure Python expression
        # implementation whenever a 'repeat' symbol is found
        kwargs = context.vars
        kwargs['repeat'] = RepeatDict(context.repeat_vars)
        kwargs["__zt_context__"] = context

        return self.template.render(**kwargs)

    @classmethod
    def cook(cls, source_file, text, engine, content_type):
        if engine is getEngine():
            def sanitize(m):
                match = m.group(1)
                logger.info(
                    'skipped "<?python%s?>" code block in '
                    'Zope 2 page template object "%s".',
                    match, source_file
                )
                return ''

            text, count = re_match_pi.subn(sanitize, text)
            if count:
                logger.warning(
                    "skipped %d code block%s (not allowed in "
                    "restricted evaluation scope)." % (
                        count, 's' if count > 1 else ''
                    )
                )

        lifetime = Lifetime()
        lifetime_ref = weakref.ref(lifetime)

        expr_types = {}
        for ty, expr in engine.types.items():
            expr_types[ty] = MappedExprType(ty, expr, engine, lifetime_ref)

        # BBB: Support CMFCore's FSPagetemplateFile formatting
        if source_file is not None and source_file.startswith('file:'):
            source_file = source_file[5:]

        if source_file is None:
            # Default to '<string>'
            source_file = ChameleonPageTemplate.filename

        template = ChPageTemplate(
            text, filename=source_file, keep_body=True,
            expression_types=expr_types,
            encoding='utf-8',
        )

        return cls(template, lifetime), template.macros
