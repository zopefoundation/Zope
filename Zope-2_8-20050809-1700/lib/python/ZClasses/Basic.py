##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Basic Item class and class manager
"""

import Globals, OFS.PropertySheets, OFS.Image, ExtensionClass
import Acquisition, Products
from zExceptions import BadRequest

class ZClassBasicSheet(OFS.PropertySheets.PropertySheet,
                       OFS.PropertySheets.View):
    """Provide management view for item classes
    """

    _getZClass=Acquisition.Acquired

    manage=Globals.DTMLFile('dtml/itemProp', globals())
    def manage_edit(self, meta_type='', icon='', file='',
                    class_id=None, title=None,
                    selected=(),
                    REQUEST=None):
        """Set basic item properties.
        """
        if meta_type: self.setClassAttr('meta_type', meta_type)

        if file and (type(file) is type('') or file.filename):
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

        if title is not None:
            self._getZClass().title=title

        if class_id is not None and class_id != self.class_id():
            self.changeClassId(class_id)

        if REQUEST is not None:
            return self.manage(
                self, REQUEST,
                manage_tabs_message='Basic properties changed')


    def classMetaType(self): return self.getClassAttr('meta_type','')

    def classIcon(self): return self.getClassAttr('icon','')

    def show_class_id(self): return True

    def class_id(self):
        return (self.getClassAttr('__module__','') or '')[1:]

    def zClassTitle(self): return self._getZClass().title

class ZClassViewsSheet(OFS.PropertySheets.PropertySheet,
                       OFS.PropertySheets.View):
    """Provide an options management view
    """

    def data(self):
        return self.getClassAttr('manage_options',(),1)

    manage=Globals.DTMLFile('dtml/views', globals())
    def manage_edit(self, actions=[], helps=[], REQUEST=None):
        "Change view actions"
        options=self.data()
        changed=0
        if len(actions)!=len(options):
            raise BadRequest, 'wrong number of actions'

        for i in range(len(actions)):
            if options[i]['action'] != actions[i]:
                options[i]['action'] = actions[i]
                changed=1
            if options[i].get('help') != (self.zclass_productid(), helps[i]):
                if helps[i]:
                    options[i]['help'] = (self.zclass_productid(), helps[i])
                    changed=1
                elif options[i].has_key('help'):
                    del options[i]['help']
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

    def zclass_productid(self):
        # find the name of the enclosing Product
        obj=self
        while hasattr(obj, 'aq_parent'):
            obj=obj.aq_parent
            try:
                if obj.meta_type=='Product':
                    return obj.id
            except:
                pass

    def manage_add(self, label, action, help, REQUEST=None):
        "Add a view"
        options=self.data()
        for option in options:
            if option['label']==label:
                raise BadRequest, (
                    'Please provide a <strong>new</strong> label.'
                    )
        if help:
            t=({'label': label, 'action': action,
                'help': (self.zclass_productid(), help)},)
        else:
            t=({'label': label, 'action': action},)
        self.setClassAttr('manage_options', tuple(options) + t)

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

    manage=Globals.DTMLFile('dtml/classPermissions', globals())

    def possible_permissions(self):
        r=map(
            lambda p: p[0],
            Products.__ac_permissions__+
            self.aq_acquire('_getProductRegistryData')('ac_permissions')
            )
        r.sort()
        return r

    def manage_edit(self, selected=[], REQUEST=None):
        "Remove some permissions"
        r=[]
        for p in (
            Products.__ac_permissions__+
            self.aq_acquire('_getProductRegistryData')('ac_permissions')):
            if p[0] in selected:
                r.append(p)

        self.setClassAttr('__ac_permissions__', tuple(r))

        if REQUEST is not None:
            return self.manage(self, REQUEST,
                           manage_tabs_message="Permissions updated")
