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

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import view_management_screens
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.special_dtml import DTMLFile
from Shared.DC.Scripts.Bindings import Bindings

class BindingsUI(Bindings):

    security = ClassSecurityInfo()

    manage_options = (
        {'label':'Bindings',
         'action':'ZBindingsHTML_editForm'},
        )

    security.declareProtected(view_management_screens,
                              'ZBindingsHTML_editForm')
    ZBindingsHTML_editForm = DTMLFile('dtml/scriptBindings', globals())

    security.declareProtected('Change bindings', 'ZBindingsHTML_editAction')
    def ZBindingsHTML_editAction(self, REQUEST):
        '''Changes binding names.
        '''
        self.ZBindings_edit(REQUEST)
        message = "Bindings changed."
        return self.manage_main(self, REQUEST, manage_tabs_message=message)

InitializeClass(BindingsUI)
