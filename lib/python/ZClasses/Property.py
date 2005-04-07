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
"""Provide management of common instance property sheets
"""

import transaction

import OFS.PropertySheets, Globals, OFS.SimpleItem, OFS.PropertyManager
import Acquisition
from AccessControl.Permission import pname

class ClassCaretaker:
    def __init__(self, klass): self.__dict__['_k']=klass
    def __getattr__(self, name): return getattr(self._k, name)
    def __setattr__(self, name, v):
        klass=self._k
        setattr(klass, name, v)
        if not getattr(klass,'_p_changed',None) and klass._p_jar is not None:
            transaction.get().register(klass)
            klass._p_changed=1
    def __delattr__(self, name):
        klass=self._k
        delattr(klass, name)
        if not getattr(klass,'_p_changed',None) and klass._p_jar is not None:
            transaction.get().register(klass)
            klass._p_changed=1


class ZCommonSheet(OFS.PropertySheets.PropertySheet, OFS.SimpleItem.Item):
    "Property Sheet that has properties common to all instances"
    meta_type="Common Instance Property Sheet"
    _properties=()

    manage_options=(
        {'label':'Properties', 'action':'manage',
         'help':('OFSP','Properties.stx')},
        {'label':'Define Permissions', 'action':'manage_security',
         'help':('OFSP','Security_Define-Permissions.stx')},
        )

    __ac_permissions__=(
        ('Manage Z Classes', ('', 'manage')),
        )

    def __init__(self, id, title):
        self.id=id
        self.title=title
        self._md={}

    def manage_afterAdd(self,item,container):
        if item is not self: return
        if self._properties:
            raise ValueError, (
                'Non-empty propertysheets cannot currently be '
                'added (or copied).<p>')

    def v_self(self):
        klass=self.aq_inner.aq_parent.aq_parent.aq_parent._zclass_
        return ClassCaretaker(klass)

    def p_self(self): return self

    def _view_widget_for_type(self, t, id):
        if t not in ('lines', 'tokens'):
            return '<dtml-var %s>' % id
        return """
        <dtml-in %s>
           <dtml-var sequence-item>
        </dtml-in %s>
        """ % (id, id)

    def manage_createView(self, id, title='', ps_view_type=None, REQUEST=None):
        """Create a view of a property sheet
        """
        if ps_view_type == 'Edit':
            return self.manage_createEditor(id, title, REQUEST)

        r=['<dtml-var standard_html_header>',
           '<table>']
        a=r.append
        for p in self.propertyMap():
            pid=p['id']
            pid=pid[:1].upper()+pid[1:]
            a('  <tr><th align=left valign=top>%s</th>' % pid)
            a('      <td align=left valign=top>%s</td>' %
              self._view_widget_for_type(p['type'], p['id'])
              )
            a('  </tr>')
        a('</table>')
        a('<dtml-var standard_html_footer>')
        r='\n'.join(r)
        self.aq_parent.aq_parent.methods.manage_addDTMLMethod(id, title, r)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(REQUEST['URL3']+'/methods/manage')

    def _edit_widget_for_type(self, t, id, p):
        if t in ('int', 'long', 'float', 'date', 'string'):
            if t=='string': q=' html_quote'
            else: q=''
            return ('''
            <input name="%s:%s" size="35"
                   value="<dtml-var %s%s>">'''
                    % (id, t, id, q)
                    )
        if t=='boolean':
            return ('''
            <input type="checkbox" name="%s:boolean" size="35"
                <dtml-if %s>CHECKED</dtml-if>>'''
                    % (id, id)
                    )

        if t=='tokens':
            return ('''
            <input type="text" name="%s:tokens" size="35"
               value="<dtml-in %s><dtml-var sequence-item> </dtml-in>">'''
                    % (id, id)
                    )

        if t=='text':
            return ('''
            <textarea name="%s:text" rows="6" cols="35"><dtml-var %s
            ></textarea>'''
                    % (id, id)
                    )

        if t=='lines':
            return ('''
            <textarea name="%s:lines" rows="6" cols="35"><dtml-in %s
            ><dtml-var sequence-item>\n</dtml-in></textarea>'''
                    % (id, id)
                    )


        if t=='selection':
            return ('''
            <dtml-if "_.has_key('%(id)s')">
            <select name="%(id)s">
              <dtml-in "_.string.split('%(select_variable)s')">
                <option
                  <dtml-if "_['sequence-item']=='%(id)s'">
                  SELECTED</dtml-if>
                  ><dtml-var sequence-item></option>
              </dtml-in>
            </select>
            <dtml-else>
              No value for %(id)s
            </dtml-if>'''
                    % p
                    )

        return ''

    def manage_beforeDelete(self, item, container):
        if self is item:
            for d in self._properties:
                self.delClassAttr(d['id'])

    def manage_createEditor(self, id, title='', REQUEST=None):
        """Create an edit interface for a property sheet
        """
        r=['<html><head><title><dtml-var title_or_id></title></head>',
           '<body bgcolor="#FFFFFF" link="#000099" vlink="#555555">',
           '<dtml-var manage_tabs>',
           '<form action="propertysheets/%s/manage_editProperties"><table>'
           % self.id]
        a=r.append
        for p in self.propertyMap():
            a('  <tr><th align=left valign=top>%s</th>' % p['id'])
            a('      <td align=left valign=top>%s</td>' %
              self._edit_widget_for_type(p['type'], p['id'], p)
              )
            a('  </tr>')
        a('  <tr><td colspan=2>')
        a('    <input type=submit value=" Change ">')
        a('    <input type=reset value=" Reset ">')
        a('  </td></tr>')
        a('</table></form>')
        a('</body></html>')
        r='\n'.join(r)
        self.aq_parent.aq_parent.methods.manage_addDTMLMethod(id, title, r)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(REQUEST['URL3']+'/methods/manage')

    def permissionMappingPossibleValues(self):
        return self.classDefinedAndInheritedPermissions()

    manage_security=Globals.DTMLFile('AccessControl/dtml/methodAccess')
    def manage_getPermissionMapping(self):
        ips=self.getClassAttr('propertysheets')
        ips=getattr(ips, self.id)

        # ugh
        perms={}
        for p in self.classDefinedAndInheritedPermissions():
            perms[pname(p)]=p

        r=[]
        for p in property_sheet_permissions:
            v=getattr(ips, pname(p))
            r.append(
                {'permission_name': p,
                 'class_permission': perms.get(v,'')
                 })

        return r

    def manage_setPermissionMapping(self, permission_names=[],
                                    class_permissions=[],
                                    REQUEST=None):
        "Change property sheet permissions"
        ips=self.getClassAttr('propertysheets')
        ips=getattr(ips, self.id)

        perms=self.classDefinedAndInheritedPermissions()
        for i in range(len(permission_names)):
            name=permission_names[i]
            p=class_permissions[i]
            if p and (p not in perms):
                __traceback_info__=perms, p, i
                raise ValueError, 'Invalid class permission'

            if name not in property_sheet_permissions: continue

            setattr(ips, pname(name), pname(p))

        if REQUEST is not None:
            return self.manage_security(
                self, REQUEST,
                manage_tabs_message='The permission mapping has been updated')

Globals.default__class_init__(ZCommonSheet)

property_sheet_permissions=(
    # 'Access contents information',
    'Manage properties',
    )

class ZInstanceSheet(OFS.PropertySheets.FixedSchema,
                     OFS.PropertySheets.View,
                    ):
    "Waaa this is too hard"

    _Manage_properties_Permission='_Manage_properties_Permission'
    _Access_contents_information_Permission='_View_Permission'

    __ac_permissions__=(
        ('Manage properties', ('manage_addProperty',
                               'manage_editProperties',
                               'manage_delProperties',
                               'manage_changeProperties',
                               'manage',
                               )),
        ('Access contents information', ('hasProperty', 'propertyIds',
                                         'propertyValues','propertyItems',
                                         'propertyMap', ''),
         ),
        )

    def v_self(self):
        return self.aq_inner.aq_parent.aq_parent

Globals.default__class_init__(ZInstanceSheet)

def rclass(klass):
    if not getattr(klass, '_p_changed', 0) and klass._p_jar is not None:
        transaction.get().register(klass)
        klass._p_changed=1

class ZInstanceSheetsSheet(OFS.Traversable.Traversable,
                           OFS.PropertySheets.View,
                           OFS.ObjectManager.ObjectManager):
    "Manage common property sheets"

    # Note that we need to make sure we add and remove
    # instance sheets.
    id='common'
    isPrincipiaFolderish=1
    icon="p_/Propertysheets_icon"
    dontAllowCopyAndPaste=1

    def tpURL(self): return 'propertysheets/common'

    def _setOb(self, id, value):
        setattr(self, id, value)
        pc=self.aq_inner.aq_parent.aq_parent._zclass_propertysheets_class
        setattr(pc,id,ZInstanceSheet(id,value))
        pc.__propset_attrs__=tuple(map(lambda o: o['id'], self._objects))
        rclass(pc)


    def _delOb(self, id):
        delattr(self, id)
        pc=self.aq_inner.aq_parent.aq_parent._zclass_propertysheets_class
        try: delattr(pc,id)
        except: pass
        pc.__propset_attrs__=tuple(map(lambda o: o['id'], self._objects))
        rclass(pc)

    meta_types=(
        Globals.Dictionary(name=ZCommonSheet.meta_type,
                           action='manage_addCommonSheetForm'),
        )

    def all_meta_types(self): return self.meta_types


    manage=Globals.DTMLFile('OFS/dtml/main',
                            management_view='Property Sheets')
    manage_main = manage
    manage_main._setName('manage_main')
    manage_addCommonSheetForm=Globals.DTMLFile('dtml/addCommonSheet',
                                               globals())

    def manage_addCommonSheet(self, id, title, REQUEST=None):
        "Add a property sheet"
        o=ZCommonSheet(id, title)
        self._setObject(id, o)
        if REQUEST is not None:
            return self.manage(self, REQUEST)

def klass_sequence(klass,attr,result=None):
    if result is None: result={}
    if hasattr(klass,attr):
        for i in getattr(klass,attr): result[i]=1
        for klass in klass.__bases__:
            klass_sequence(klass, attr, result)
    return result

class ZInstanceSheets(OFS.PropertySheets.PropertySheets, Globals.Persistent):
    " "
    __propset_attrs__=()
    _implements_the_notional_subclassable_propertysheet_class_interface=1

    def __propsets__(self):
        propsets=ZInstanceSheets.inheritedAttribute('__propsets__')(self)
        r=[]
        for id in klass_sequence(self.__class__,'__propset_attrs__').keys():
            r.append(getattr(self, id))
        return propsets+tuple(r)


Globals.default__class_init__(ZInstanceSheets)
