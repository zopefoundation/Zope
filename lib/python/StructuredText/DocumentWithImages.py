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

from zope.structuredtext.stng import StructuredTextImage
from zope.structuredtext.document import DocumentWithImages

from zope.deprecation import deprecated
deprecated("StructuredTextImage",
           'The StructuredText package is deprecated and will be removed '
           'in Zope 2.12. Use zope.structuredtext.stng.StructuredTextImage '
           'instead.')
deprecated("DocumentWithImages",
           'The StructuredText package is deprecated and will be removed '
           'in Zope 2.12. Use zope.structuredtext.document.DocumentWithImages '
           'instead.')
