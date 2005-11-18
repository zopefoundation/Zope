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
from Bindings import Bindings

class BindingsUI(Bindings):

    manage_options = (
        {'label':'Bindings',
         'action':'ZBindingsHTML_editForm',
         'help':('PythonScripts', 'Bindings.stx')},
        )

    __ac_permissions__ = (
        ('View management screens', ('ZBindingsHTML_editForm',)),
        ('Change bindings', ('ZBindingsHTML_editAction',)),
        )

    ZBindingsHTML_editForm = Globals.DTMLFile('dtml/scriptBindings', globals())

    def ZBindingsHTML_editAction(self, REQUEST):
        '''Changes binding names.
        '''
        self.ZBindings_edit(REQUEST)
        message = "Bindings changed."
        return self.manage_main(self, REQUEST, manage_tabs_message=message)

Globals.default__class_init__(BindingsUI)
