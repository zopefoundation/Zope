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

from urllib.parse import quote

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import view_management_screens
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.special_dtml import DTMLFile
from DocumentTemplate._DocumentTemplate import TemplateDict
from OFS.SimpleItem import SimpleItem
from Shared.DC.Scripts.Bindings import defaultBindings  # NOQA
from Shared.DC.Scripts.BindingsUI import BindingsUI
from Shared.DC.Scripts.Signature import FuncCode  # NOQA
from zExceptions import Redirect


class Script(SimpleItem, BindingsUI):
    """Web-callable script mixin
    """

    security = ClassSecurityInfo()

    index_html = None
    __code__ = None
    __defaults__ = ()

    _Bindings_ns_class = TemplateDict

    security.declareProtected(view_management_screens,  # NOQA: D001
                              'ZScriptHTML_tryForm')
    ZScriptHTML_tryForm = DTMLFile('dtml/scriptTry', globals())

    def ZScriptHTML_tryAction(self, REQUEST, argvars):
        """Apply the test parameters.
        """
        vv = []
        for argvar in argvars:
            if argvar.value:
                vv.append(f"{quote(argvar.name)}={quote(argvar.value)}")
        raise Redirect(f"{REQUEST['URL1']}?{'&'.join(vv)}")

    from .Signature import _setFuncSignature


InitializeClass(Script)
