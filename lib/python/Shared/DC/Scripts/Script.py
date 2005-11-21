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

"""Script module

This provides generic script support
"""

__version__='$Revision$'[11:-2]

from Globals import InitializeClass
from Globals import DTMLFile
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens
from OFS.SimpleItem import SimpleItem
from string import join
from urllib import quote
from BindingsUI import BindingsUI
from Bindings import defaultBindings
from DocumentTemplate.DT_Util import TemplateDict
from zExceptions import Redirect

# Temporary:
from Signature import FuncCode

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
