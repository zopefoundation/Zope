"""``chameleon`` integration.

The engine returned  by the template's ``pt_getEngine`` decides
whether the ``zope.tales`` or
the ``chameleon.tales`` TALES implementation is used:
``zope.tales`` is used when the engine is an instance of
``zope.pagetemplate.enging.ZopeBaseEngine``,
``chameleon.tales`` otherwise. This could get more flexible
in the future.
"""

import ast
import logging
import re
from collections.abc import Mapping
from weakref import ref

from chameleon.astutil import Static
from chameleon.astutil import Symbol
from chameleon.codegen import template
from chameleon.exc import ExpressionError
from chameleon.tal import RepeatDict
from chameleon.tales import DEFAULT_MARKER  # only in chameleon 3.8.0 and up
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

from .Expressions import PathIterator
from .Expressions import SecureModuleImporter
from .interfaces import IZopeAwareEngine


class _PseudoContext:
    """auxiliary context object.

    Used to bridge between ``chameleon`` and ``zope.tales`` iterators.
    """
    @staticmethod
    def setLocal(*args):
        pass


class RepeatDictWrapper(RepeatDict):
    """Wrap ``chameleon``s ``RepeatDict``.

    Aims:

      1. make it safely usable by untrusted code

      2. let it use a ``zope.tales`` compatible ``RepeatItem``
    """

    security = ClassSecurityInfo()
    security.declareObjectPublic()
    security.declarePrivate(  # NOQA: D001
        *(set(dir(RepeatDict)) - set(dir(MultiMapping))))  # NOQA: D001
    __allow_access_to_unprotected_subobjects__ = True

    # Logic (mostly) from ``chameleon.tal.RepeatDict``
    def __call__(self, key, iterable):
        """We coerce the iterable to a tuple and return an iterator
        after registering it in the repeat dictionary."""
        iterable = list(iterable) if iterable is not None else ()

        length = len(iterable)

        # Insert as repeat item
        ri = self[key] = RepeatItem(None, iterable, _PseudoContext)

        return ri, length


InitializeClass(RepeatDictWrapper)


class RepeatItem(PathIterator):
    """Iterator compatible with ``chameleon`` and ``zope.tales``."""
    def __iter__(self):
        return self

    def __next__(self):
        if super().__next__():
            return self.item
        else:
            raise StopIteration


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


# map context class to context wrapper class
_context_class_registry = {}


def _with_vars_from_chameleon(context):
    """prepare *context* to get its ``vars`` from ``chameleon``."""
    cc = context.__class__
    wc = _context_class_registry.get(cc)
    if wc is None:
        class ContextWrapper(_C2ZContextWrapperBase, cc):
            pass

        wc = _context_class_registry[cc] = ContextWrapper
    context.__class__ = wc
    return ref(context)


class Name2KeyError(Mapping):
    # auxiliary class to convert ``chameleon``'s ``NameError``
    # into ``KeyError``
    def __init__(self, mapping):
        self.data = mapping

    def __getitem__(self, key):
        try:
            return self.data[key]
        except NameError:
            raise KeyError(key)

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)


class _C2ZContextWrapperBase:
    """Behaves like "zope" context with vars from "chameleon" context.

    It is assumed that an instance holds the current ``chameleon``
    context in its attribute ``_c_context``.
    """
    @property
    def vars(self):
        return Name2KeyError(self._c_context)

    # delegate to `_c_context`
    def getValue(self, name, default=None):
        try:
            return self._c_context[name]
        except (NameError, KeyError):
            return default

    get = getValue

    def setLocal(self, name, value):
        self._c_context.setLocal(name, value)

    def setGlobal(self, name, value):
        self._c_context.setGlobal(name, value)

    # unsupported methods
    def beginScope(self, *args, **kw):
        """will not work as the scope is controlled by ``chameleon``."""
        raise NotImplementedError()

    endScope = beginScope
    setSourceFile = beginScope
    setPosition = beginScope
    setRepeat = beginScope

    # work around bug in ``zope.tales.tales.Context``
    def getDefault(self):
        return self.contexts["default"]


def _C2ZContextWrapper(c_context, attrs):
    c_context["attrs"] = attrs
    zt_context = c_context["__zt_context__"]()
    zt_context._c_context = c_context
    return zt_context


_c_context_2_z_context_node = Static(Symbol(_C2ZContextWrapper))


# exclude characters special for ``chameleon``'s interpolation syntax
# from use in path expressions to reduce the failure risk
# for the ``chameleon`` interpolation heuristics
BAD_PATH_CHARS = "${}"
contains_bad_path_chars = re.compile("[%s]" % BAD_PATH_CHARS).search


class MappedExpr:
    """map expression: ``zope.tales`` --> ``chameleon.tales``."""
    def __init__(self, type, expression, zt_engine):
        self.type = type
        # At this place, *expression* is a `chameleon.tokenize.Token`
        # (a subtype of `str` for PY3 and of `unicode` for PY2).
        # The ``_compile_zt_expr`` below causes this to be cached
        # which can lead under Python 3 to unsolicited translations
        # (details "https://github.com/zopefoundation/Zope/issues/876")
        # To avoid this, call ``_compile_zt_expr`` with
        # *expression* cast to the `Token` base type.
        expr = str(expression)
        self.expression = expression
        # compile to be able to report errors
        compiler_error = zt_engine.getCompilerError()
        try:
            zt_expr = _compile_zt_expr(type, expr, engine=zt_engine)
        except compiler_error as e:
            raise ExpressionError(str(e), self.expression)
        if (self.type == "path"
                and isinstance(zt_expr, PathExpr)
                and contains_bad_path_chars(self.expression)):
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
            #   resulting problems: forbid special characters
            #   for interpolation in ``SubPathExpr``s.
            for se in zt_expr._subexprs:
                # dereference potential evaluation method
                se = getattr(se, "__self__", se)
                # we assume below that expressions other than
                # ``SubPathExpr`` have flagged out use of the special
                # characters already
                # we know that this assumption is wrong in some cases
                if isinstance(se, SubPathExpr):
                    for pe in se._compiled_path:
                        if isinstance(pe, tuple):  # standard path
                            for spe in pe:
                                if contains_bad_path_chars(spe):
                                    raise ExpressionError(
                                        "%s unsupported",
                                        BAD_PATH_CHARS)

    def __call__(self, target, c_engine):
        # The convoluted handling of ``attrs`` below was necessary
        # for some ``chameleon`` versions to work around
        # "https://github.com/malthe/chameleon/issues/323".
        # The work round is partial only: until the ``chameleon``
        # problem is fixed, `attrs` cannot be used inside ``tal:define``.
        # Potentially, ``attrs`` handling could be simplified
        # for ``chameleon > 3.8.0``.
        return template(
            "try: __zt_tmp = attrs\n"
            "except NameError: __zt_tmp = None\n"
            "target = compile_zt_expr(type, expression, econtext=econtext)"
            "(c2z_context(econtext, __zt_tmp))",
            target=target,
            compile_zt_expr=_compile_zt_expr_node,
            type=ast.Str(self.type),
            expression=ast.Str(self.expression),
            c2z_context=_c_context_2_z_context_node,
            attrs=ast.Name("attrs", ast.Load()))


class MappedExprType:
    """map expression type: ``zope.tales`` --> ``chameleon.tales``."""
    def __init__(self, engine, type):
        self.engine = engine
        self.type = type

    def __call__(self, expression):
        return MappedExpr(self.type, expression, self.engine)


class ZtPageTemplate(ChameleonPageTemplate):
    """``ChameleonPageTemplate`` using ``zope.tales.tales._default``.

    Note: this is not necessary when ``chameleon.tales`` is used
    but it does not hurt to use the fixed value to represent ``default``
    rather than a template specific value.
    """

    # use `chameleon` configuration to obtain more
    # informative error information
    value_repr = staticmethod(repr)


@implementer(IPageTemplateProgram)
@provider(IPageTemplateEngine)
class Program:

    def __init__(self, template, engine):
        self.template = template
        self.engine = IZopeAwareEngine(engine, engine)

    def __call__(self, context, macros, tal=True, **options):
        if tal is False:
            return self.template.body

        # Swap out repeat dictionary for Chameleon implementation
        kwargs = context.vars
        kwargs['repeat'] = RepeatDictWrapper(context.repeat_vars)
        # provide context for ``zope.tales`` expression compilation
        #   and evaluation
        #   unused for ``chameleon.tales`` expressions
        kwargs["__zt_engine__"] = self.engine
        kwargs["__zt_context__"] = _with_vars_from_chameleon(context)

        template = self.template
        # ensure ``chameleon`` ``default`` representation
        context.setContext("default", DEFAULT_MARKER)
        kwargs["default"] = DEFAULT_MARKER

        return template.render(**kwargs)

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
            expr_types = {ty: MappedExprType(engine, ty)
                          for ty in engine.types}
        else:
            # use ``chameleon.tales`` expressions
            expr_types = engine.types

        # BBB: Support CMFCore's FSPagetemplateFile formatting
        if source_file is not None and source_file.startswith('file:'):
            source_file = source_file[5:]

        if source_file is None:
            # Default to '<string>'
            source_file = ChameleonPageTemplate.filename

        zope_version = getZopeVersion()
        template = ZtPageTemplate(
            text, filename=source_file, keep_body=True,
            expression_types=expr_types,
            encoding='utf-8',
            extra_builtins={
                "modules": SecureModuleImporter,
                # effectively invalidate the template file cache for
                #   every new ``Zope`` version
                "zope_version_" + "_".join(
                    str(c) for c in zope_version
                    if not (isinstance(c, int) and c < 0)): getZopeVersion}
        )

        return cls(template, engine), template.macros
