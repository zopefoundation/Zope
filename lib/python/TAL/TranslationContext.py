##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Translation context object for the TALInterpreter's I18N support.

The translation context provides a container for the information
needed to perform translation of a marked string from a page template.

$Id$
"""

DEFAULT_DOMAIN = "default"

class TranslationContext:
    """Information about the I18N settings of a TAL processor."""

    def __init__(self, parent=None, domain=None, target=None, source=None):
        if parent:
            if not domain:
                domain = parent.domain
            if not target:
                target = parent.target
            if not source:
                source = parent.source
        elif domain is None:
            domain = DEFAULT_DOMAIN

        self.parent = parent
        self.domain = domain
        self.target = target
        self.source = source
