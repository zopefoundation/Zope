##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""Basic Item class and class manager
"""

import Globals, OFS.PropertySheets, OFS.Image, ExtensionClass
from string import split, join, strip

class ZClassBasicSheet(OFS.PropertySheets.PropertySheet,
                       OFS.PropertySheets.View):
    """Provide management view for item classes
    """

    manage=Globals.HTMLFile('itemProp', globals())
    def manage_edit(self, meta_type='', icon='', file='', REQUEST=None):
        """Set basic item properties.
        """
        if meta_type: self.setClassAttr('meta_type', meta_type)

        if file and hasattr(file, 'content_type'):
            __traceback_info__=file
            image=self.getClassAttr('ziconImage', None)
            if image is None:
                self.setClassAttr('ziconImage',
                                  OFS.Image.Image('ziconImage','',file))
            else:
                image.manage_upload(file)
                        
            if (not icon) and REQUEST:
                icon=(REQUEST['URL3'][len(REQUEST['BASE1'])+1:]
                      +'/ziconImage')
            
        self.setClassAttr('icon', icon)

        if REQUEST is not None:
            return self.manage(
                self, REQUEST,
                manage_tabs_message='Basic properties changed')


    def icon(self):
        return self.getClassAttr('icon','')

    def meta_type(self):
        return self.getClassAttr('meta_type','')

class ZClassViewsSheet(OFS.PropertySheets.PropertySheet,
                       OFS.PropertySheets.View):
    """Provide an options management view
    """

    def data(self):
        return self.getClassAttr('manage_options',(),1)

    manage=Globals.HTMLFile('views', globals())
    def manage_edit(self, actions=[], REQUEST=None):
        "Change view actions"
        options=self.data()
        changed=0
        if len(actions)!=len(options):
            raise 'Bad Request', 'wrong number of actions'

        for i in range(len(actions)):
            if options[i]['action'] != actions[i]:
                options[i]['action'] = actions[i]
                changed=1
                
        if changed:
            self.setClassAttr('manage_options', options)
            message='The changes were saved.'
        else:
            message='No changes were required.'
        
        if REQUEST is not None:
            return self.manage(
                self, REQUEST, manage_tabs_message=message)

    def manage_delete(self, selected=[], REQUEST=None):
        "Delete one or more views"
        options=self.data()
        newoptions=filter(
            lambda d, selected=selected:
            d['label'] not in selected,
            options)
        if len(options) != len(newoptions):
            self.setClassAttr('manage_options', tuple(newoptions))
            message='Views deleted'
        else:
            message='No views were selected for deletion'
        
        if REQUEST is not None:
            return self.manage(
                self, REQUEST, manage_tabs_message=message)

    def manage_add(self, label, action, REQUEST=None):
        "Add a view"
        options=self.data()
        for option in options:
            if option['label']==label:
                raise 'Bad Request', (
                    'Please provide a <strong>new</strong> label.'
                    )
        self.setClassAttr('manage_options',
                          tuple(options)+({'label': label, 'action': action},))
        
        if REQUEST is not None:
            return self.manage(
                self, REQUEST,
                manage_tabs_message='View %s has been added' % label)

    def manage_first(self, selected=[], REQUEST=None):
        "Make some views first"
        options=self.data()
        if not selected:
            message="No views were selected to be made first."
        elif len(selected)==len(options):
            message="Making all views first has no effect."
        else:
            options=self.data()
            options=tuple(
                filter(lambda option, selected=selected:
                       option['label'] in selected,
                       options)
                +
                filter(lambda option, selected=selected:
                       option['label'] not in selected,
                       options)
                )
            self.setClassAttr('manage_options', options)
            message="Views were rearranged as requested."

        if REQUEST is not None:
            return self.manage(
                self, REQUEST, manage_tabs_message=message)        
        

class ZClassPermissionsSheet(OFS.PropertySheets.PropertySheet,
                             OFS.PropertySheets.View):
    "Manage class permissions"
        
    manage=Globals.HTMLFile('classPermissions', globals())

    def manage_delete(self, selected=[], REQUEST=None):
        "Remove some permissions"
        perms=self.classDefinedPermissions()
        changed=0
        message=[]
        for s in selected:
            if s in perms:
                perms.remove(s)
                changed=1
            else: message.append('Invalid permission: %s' % s)
                
        if changed:
            self.setClassAttr(
                '__ac_permissions__',
                tuple(map(lambda p: (p,()), perms))
                )
        else:
            message.append('Permissions are unchanged.')

        if message: message=join(message, '<br>\n')

        return self.manage(self, REQUEST, manage_tabs_message=message)

    def manage_add(self, REQUEST, newPermission=''):
        "Remove some permissions"
        perms=self.classDefinedPermissions()
        changed=0
        message=[]

        newPermission=strip(newPermission)
        if newPermission:
            if newPermission in perms:
                message.append('The new permission, %s, is already in use' % s)
            else:
                perms.append(newPermission)
                changed=1
                
        if changed:
            self.setClassAttr(
                '__ac_permissions__',
                tuple(map(lambda p: (p,()), perms))
                )
        else:
            message.append('Permissions are unchanged.')
        if message: message=join(message, '<br>\n')
        return self.manage(self, REQUEST, manage_tabs_message=message)
        
    
