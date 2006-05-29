"""Interface that a TALES engine provides to the METAL/TAL implementation."""

import zope.deferredimport
zope.deferredimport.deprecatedFrom(
    "The TAL implementation has moved to zope.tal.  Import expression "
    "interfaces from zope.tal.interfaces.  The old references will be "
    "gone in Zope 2.12.",
    'zope.tal.interfaces'
    'ITALExpressionCompiler', 'ITALExpressionEngine', 'ITALExpressionErrorInfo'
    )

