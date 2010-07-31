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

from string import join
from urllib import quote

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import view_management_screens
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.special_dtml import DTMLFile
from DocumentTemplate.DT_Util import TemplateDict
from OFS.SimpleItem import SimpleItem
from zExceptions import Redirect

from Shared.DC.Scripts.BindingsUI import BindingsUI
from Shared.DC.Scripts.Bindings import defaultBindings
# Temporary:
from Shared.DC.Scripts.Signature import FuncCode

class Script(SimpleItem, BindingsUI):
    """Web-callable script mixin
    """

    security = ClassSecurityInfo()

    index_html = None
    func_defaults=()
    func_code=None

    _Bindings_ns_class = TemplateDict

    security.declareProtected(view_management_screens, 'ZScriptHTML_tryForm')
    ZScriptHTML_tryForm = DTMLFile('dtml/scriptTry', globals())

    def ZScriptHTML_tryAction(self, REQUEST, argvars):
        """Apply the test parameters.
        """
        vv = []
        for argvar in argvars:
            if argvar.value:
                vv.append("%s=%s" % (quote(argvar.name), quote(argvar.value)))
        raise Redirect, "%s?%s" % (REQUEST['URL1'], join(vv, '&'))

    from Signature import _setFuncSignature

InitializeClass(Script)
