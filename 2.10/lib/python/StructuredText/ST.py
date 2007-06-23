##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from zope.structuredtext.stng import \
     indention, insert, display, display2, findlevel
from zope.structuredtext.stng import structurize as StructuredText
from zope.structuredtext.stng import \
     StructuredTextParagraph, StructuredTextDocument
Basic = StructuredText

from zope.deprecation import deprecated
deprecated(("StructuredText", "Basic"),
           'The StructuredText package is deprecated and will be removed '
           'in Zope 2.12. Use zope.structuredtext.stng.structurize '
           'instead.')
deprecated("StructuredTextParagraph",
           'The StructuredText package is deprecated and will be removed '
           'in Zope 2.12. Use zope.structuredtext.stng.StructuredTextParagraph '
           'instead.')
deprecated("StructuredTextDocument",
           'The StructuredText package is deprecated and will be removed '
           'in Zope 2.12. Use zope.structuredtext.stng.StructuredTextDocument '
           'instead.')
