##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Simple content class(es) for browser tests
"""

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from zope.interface import Interface
from zope.interface import implementer


class ISimpleContent(Interface):
    pass


class ICallableSimpleContent(ISimpleContent):
    pass


class IIndexSimpleContent(ISimpleContent):
    pass


@implementer(ISimpleContent)
class SimpleContent(SimpleItem):

    meta_type = 'Five SimpleContent'
    security = ClassSecurityInfo()

    def __init__(self, id, title):
        self.id = id
        self.title = title

    @security.public
    def mymethod(self):
        return "Hello world"

    @security.public
    def direct(self):
        """Should be able to traverse directly to this as there is no view.
        """
        return "Direct traversal worked"


InitializeClass(SimpleContent)


@implementer(ICallableSimpleContent)
class CallableSimpleContent(SimpleItem):
    """A Viewable piece of content"""

    meta_type = "Five CallableSimpleContent"

    def __call__(self, *args, **kw):
        """ """
        return "Default __call__ called"


InitializeClass(CallableSimpleContent)


@implementer(IIndexSimpleContent)
class IndexSimpleContent(SimpleItem):
    """A Viewable piece of content"""

    meta_type = 'Five IndexSimpleContent'

    def index_html(self, *args, **kw):
        """ """
        return "Default index_html called"


InitializeClass(IndexSimpleContent)


def manage_addSimpleContent(self, id, title, REQUEST=None):
    """Add the simple content."""
    self._setObject(id, SimpleContent(id, title))


def manage_addCallableSimpleContent(self, id, title, REQUEST=None):
    """Add the viewable simple content."""
    self._setObject(id, CallableSimpleContent(id, title))


def manage_addIndexSimpleContent(self, id, title, REQUEST=None):
    """Add the viewable simple content."""
    self._setObject(id, IndexSimpleContent(id, title))
