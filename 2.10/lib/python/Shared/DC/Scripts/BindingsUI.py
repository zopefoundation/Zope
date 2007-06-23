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

__version__='$Revision$'[11:-2]

import Globals
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens
from Bindings import Bindings

class BindingsUI(Bindings):

    security = ClassSecurityInfo()

    manage_options = (
        {'label':'Bindings',
         'action':'ZBindingsHTML_editForm',
         'help':('PythonScripts', 'Bindings.stx')},
        )

    security.declareProtected(view_management_screens,
                              'ZBindingsHTML_editForm')
    ZBindingsHTML_editForm = Globals.DTMLFile('dtml/scriptBindings', globals())

    security.declareProtected('Change bindings', 'ZBindingsHTML_editAction')
    def ZBindingsHTML_editAction(self, REQUEST):
        '''Changes binding names.
        '''
        self.ZBindings_edit(REQUEST)
        message = "Bindings changed."
        return self.manage_main(self, REQUEST, manage_tabs_message=message)

InitializeClass(BindingsUI)
