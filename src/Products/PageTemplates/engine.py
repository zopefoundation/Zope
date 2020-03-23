"""``chameleon`` integration.

We use the ``zope.tales`` expression implementation (as adapted for ``Zope``)
not that of ``chameleon.tales``.
"""

import ast
import copy
import logging
import re

from chameleon.astutil import Static
from chameleon.astutil import Symbol
from chameleon.codegen import template
from chameleon.exc import ExpressionError
from chameleon.tal import RepeatDict
from chameleon.zpt.template import Macros

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.version_txt import getZopeVersion
from MultiMapping import MultiMapping
from z3c.pt.pagetemplate import PageTemplate as ChameleonPageTemplate
from zope.interface import implementer
from zope.interface import provider
from zope.pagetemplate.engine import ZopeBaseEngine
from zope.pagetemplate.interfaces import IPageTemplateEngine
from zope.pagetemplate.interfaces import IPageTemplateProgram
from zope.tales.expressions import PathExpr
from zope.tales.expressions import SubPathExpr

from .Expressions import SecureModuleImporter


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
#  and includes it in the byte code generated for the complete
#  template. In production mode, the whole is cached
#  in a long term (across process invocations) file system based
#  cache, keyed with the digest of the template's source and
#  some names.
#  ``zope.tales`` expressions are essentially runtime objects
#  (general "callables", usually class instances with a ``__call__``
#  method. They cannot be (easily) represented via byte code.
#  We address this problem by representing such an expression
#  in the byte code as a function call to compile the expression.
#  For efficiency, a (process local) compile cache is used
#  to cache compilation results, the ``zt_expr_registry``,
#  keyed by the engine id, the expression type and the expression source.

_zt_expr_registry = {}


def _compile_zt_expr(type, expression, engine=None, econtext=None):
    """compile *expression* of type *type*.

    The engine is derived either directly from *engine* or the
    execution content *econtext*. One of them must be given.

    The compilation result is cached in ``_zt_expr_registry``.
    """
    if engine is None:
        engine = econtext["__zt_engine__"]
    key = id(engine), type, expression
    # cache lookup does not need to be protected by locking
    #  (but we could potentially prevent unnecessary computations)
    expr = _zt_expr_registry.get(key)
    if expr is None:
        expr = engine.types[type](type, expression, engine)
        _zt_expr_registry[key] = expr
    return expr


_compile_zt_expr_node = Static(Symbol(_compile_zt_expr))


def _c_context_2_z_context(c_context):
    z_context = copy.copy(c_context["__zt_context__"])
    # not sure that ``lazy`` works as expected
    # An upcoming ``chameleon`` version will (potentially) have
    #   a ``root`` attribute with global assignments.
    #   Uncomment the code below once ``Zope`` uses such a version.
    #   The code is not yet active because we cannot yet test it.
#    root = getattr(c_context, "root", None)
#    if root is not None:
#        z_context.vars = dict(root.vars)
#        z_context.vars.update(c_context.vars)
#    else:
#        z_context.vars = dict(c_context.vars)
    # Comment the line below once the comment block above is uncommented
    z_context.vars = dict(c_context.vars)
    return z_context


_c_context_2_z_context_node = Static(Symbol(_c_context_2_z_context))


class MappedExpr(object):
    """map expression: ``zope.tales`` --> ``chameleon.tales``."""
    def __init__(self, type, expression, zt_engine):
        self.type = type
        self.expression = expression
        # compile to be able to report errors
        compiler_error = zt_engine.getCompilerError()
        try:
            zt_expr = _compile_zt_expr(type, expression, engine=zt_engine)
        except compiler_error as e:
            raise ExpressionError(str(e), self.expression)
        if (self.type == "path" and "$" in self.expression
                and isinstance(zt_expr, PathExpr)):
            # the ``chameleon`` template engine has a really curious
            #   implementation of global ``$`` interpolation
            #   (see ``chameleon.compiler.Interpolator``):
            #   when it sees ``${``, it starts with the largest
            #   substring starting at this position and ending in ``}``
            #   and tries to generate code for it. If this fails, it
            #   retries with the second largest such substring, etc.
            # Of course, this fails with ``zope.tales`` ``path`` expressions
            #   where almost any character is syntactically legal.
            #   Thus, it happily generates code for e.g.
            #   ``d/a} ${d/b`` (resulting from ``${d/a} ${d/b}``)
            #   but its evaluation will fail (with high likelyhood).
            # We use a heuristics here to handle many (but not all)
            #   resulting problems: forbid ``$`` in ``SubPathExpr``s.
            for se in zt_expr._subexprs:
                # dereference potential evaluation method
                se = getattr(se, "__self__", se)
                # we assume below that expressions other than
                # ``SubPathExpr`` have flagged out ``$`` use already
                # we know that this assumption is wrong in some cases
                if isinstance(se, SubPathExpr):
                    for pe in se._compiled_path:
                        if isinstance(pe, tuple):  # standard path
                            for spe in pe:
                                if "$" in spe:
                                    raise ExpressionError("$ unsupported", spe)

    def __call__(self, target, c_engine):
        return template(
            "target = compile_zt_expr(type, expression, econtext=econtext)"
            "(c2z_context(econtext))",
            target=target,
            compile_zt_expr=_compile_zt_expr_node,
            type=ast.Str(self.type),
            expression=ast.Str(self.expression),
            c2z_context=_c_context_2_z_context_node)


class MappedExprType(object):
    """map expression type: ``zope.tales`` --> ``chameleon.tales``."""
    def __init__(self, engine, type):
        self.engine = engine
        self.type = type

    def __call__(self, expression):
        return MappedExpr(self.type, expression, self.engine)


class ZtPageTemplate(ChameleonPageTemplate):
    """``ChameleonPageTemplate`` for use with ``zope.tales`` expressions."""

    # override to get the proper ``zope.tales`` default marker
    def _compile(self, body, builtins):
        code = super(ZtPageTemplate, self)._compile(body, builtins)
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

    def __init__(self, template, engine):
        self.template = template
        self.engine = engine

    def __call__(self, context, macros, tal=True, **options):
        if tal is False:
            return self.template.body

        # Swap out repeat dictionary for Chameleon implementation
        kwargs = context.vars
        kwargs['repeat'] = RepeatDict(context.repeat_vars)
        # provide context for ``zope.tales`` expression compilation
        #   and evaluation
        #   unused for ``chameleon.tales`` expressions
        kwargs["__zt_engine__"] = self.engine
        kwargs["__zt_context__"] = context

        return self.template.render(**kwargs)

    @classmethod
    def cook(cls, source_file, text, engine, content_type):
        if getattr(engine, "untrusted", False):
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

        if isinstance(engine, ZopeBaseEngine):
            # use ``zope.tales`` expressions
            expr_types = dict((ty, MappedExprType(engine, ty))
                              for ty in engine.types)
            template_class = ZtPageTemplate
        else:
            # use ``chameleon.tales`` expressions
            expr_types = engine.types
            template_class = ChameleonPageTemplate

        # BBB: Support CMFCore's FSPagetemplateFile formatting
        if source_file is not None and source_file.startswith('file:'):
            source_file = source_file[5:]

        if source_file is None:
            # Default to '<string>'
            source_file = ChameleonPageTemplate.filename

        template = template_class(
            text, filename=source_file, keep_body=True,
            expression_types=expr_types,
            encoding='utf-8',
            extra_builtins={
                "modules": SecureModuleImporter,
                # effectively invalidate the template file cache for
                #   every new ``Zope`` version
                "zope_version_" + "_".join(
                    str(c) for c in getZopeVersion()
                    if not (isinstance(c, int) and c < 0)): getZopeVersion}
        )

        return cls(template, engine), template.macros
