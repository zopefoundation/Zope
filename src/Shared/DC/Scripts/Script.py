##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Script module

This provides generic script support
"""

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from DocumentTemplate.DT_Util import TemplateDict
from OFS.SimpleItem import SimpleItem

from Shared.DC.Scripts.BindingsUI import BindingsUI

from Shared.DC.Scripts.Bindings import defaultBindings  # NOQA
from Shared.DC.Scripts.Signature import FuncCode  # NOQA


class Script(SimpleItem, BindingsUI):
    """Web-callable script mixin
    """

    security = ClassSecurityInfo()

    index_html = None
    __code__ = None
    __defaults__ = ()

    _Bindings_ns_class = TemplateDict
    from .Signature import _setFuncSignature

InitializeClass(Script)
