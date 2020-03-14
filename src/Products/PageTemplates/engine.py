"""``chameleon`` template engine integration."""


import logging
import re

from chameleon.tal import RepeatDict
from chameleon.zpt.template import Macros

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Products.PageTemplates import ZRPythonExpr
from Products.PageTemplates.expression import getEngine
from z3c.pt.pagetemplate import PageTemplate as ChameleonPageTemplate
from zope.interface import implementer
from zope.interface import provider
from zope.pagetemplate.interfaces import IPageTemplateEngine
from zope.pagetemplate.interfaces import IPageTemplateProgram

from .expression import ZopeEngine
from .expression import createTrustedZopeEngine


# Declare Chameleon's repeat dictionary public
RepeatDict.security = ClassSecurityInfo()
RepeatDict.security.declareObjectPublic()
RepeatDict.__allow_access_to_unprotected_subobjects__ = True

InitializeClass(RepeatDict)

# Declare Chameleon Macros object accessible
# This makes subscripting work, as in template.macros['name']
Macros.__allow_access_to_unprotected_subobjects__ = True

re_match_pi = re.compile(r'<\?python([^\w].*?)\?>', re.DOTALL)
logger = logging.getLogger('Products.PageTemplates')


@implementer(IPageTemplateProgram)
@provider(IPageTemplateEngine)
class Program(object):

    extra_builtins = {
        'modules': ZRPythonExpr._SecureModuleImporter()
    }

    def __init__(self, template):
        self.template = template

    def __call__(self, context, macros, tal=True, **options):
        if tal is False:
            return self.template.body

        # Swap out repeat dictionary for Chameleon implementation
        # and store wrapped dictionary in new variable -- this is
        # in turn used by the secure Python expression
        # implementation whenever a 'repeat' symbol is found
        kwargs = context.vars
        kwargs['wrapped_repeat'] = kwargs['repeat']
        kwargs['repeat'] = RepeatDict(context.repeat_vars)

        return self.template.render(**kwargs)

    @classmethod
    def cook(cls, source_file, text, engine, content_type):
        if not isinstance(engine, ZopeEngine):
            # HACK
            #  The ``chameleoon`` integration happens at the
            #  ``zope.pagetemplate`` level.
            #  There are users (e.g. ``z3c.form``) which use templates
            #  directly from ``zope.pagetemplate`` and are unaware
            #  of the switch to ``chameleon`` and its special
            #  TALES engine requirements. As a consequence, they
            #  provide a wrong *engine*.
            #  We ignore *engine* is this case and replace it
            #  with a trusted engine compatible with ``chameleon``.
            #
            #  This is compatible with the previous behaviour
            #  (hacky, too) which used *engine* only to check
            #  against ``getEngine()`` and use the trusted engine
            #  if not identical.
            engine = createTrustedZopeEngine()
        elif engine is getEngine():
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

        expression_types = engine.types

        # BBB: Support CMFCore's FSPagetemplateFile formatting
        if source_file is not None and source_file.startswith('file:'):
            source_file = source_file[5:]

        if source_file is None:
            # Default to '<string>'
            source_file = ChameleonPageTemplate.filename

        template = ChameleonPageTemplate(
            text, filename=source_file, keep_body=True,
            expression_types=expression_types,
            encoding='utf-8', extra_builtins=cls.extra_builtins,
        )

        return cls(template), template.macros
