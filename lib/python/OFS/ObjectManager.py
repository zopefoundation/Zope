##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################
__doc__="""Object Manager

$Id: ObjectManager.py,v 1.48 1998/12/04 20:15:30 jim Exp $"""

__version__='$Revision: 1.48 $'[11:-2]

import App.Management, Acquisition, App.Undo, Globals
import App.FactoryDispatcher
from Globals import HTMLFile, HTMLFile, Persistent
from Globals import MessageDialog, default__class_init__
from string import find,join,lower,split
from urllib import quote
from DocumentTemplate import html_quote
from ZPublisher.Converters import type_converters
from DateTime import DateTime

class ObjectManager(
    App.Management.Navigation,
    App.Management.Tabs,
    Acquisition.Implicit,
    Persistent,
    App.Undo.UndoSupport,
    ):
    """Generic object manager

    This class provides core behavior for collections of heterogeneous objects. 
    """

    meta_type  ='ObjectManager'
    meta_types = dynamic_meta_types = ()
    id       ='default'
    title=''
    icon='p_/folder'
    _objects   =()
    _properties =({'id':'title', 'type': 'string'},)

    manage_main          =HTMLFile('main', globals())
    manage_propertiesForm=HTMLFile('properties', globals())

    manage_options=(
    {'icon':icon,              'label':'Objects',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'OFS/Properties_icon.gif', 'label':'Properties',
     'action':'manage_propertiesForm',   'target':'manage_main'},
    {'icon':'OFS/Help_icon.gif', 'label':'Help',
     'action':'manage_help',   'target':'_new'},
    )

    isAnObjectManager=1

    isPrincipiaFolderish=1

    def __class_init__(self):
        try:    mt=list(self.meta_types)
        except: mt=[]
        for b in self.__bases__:
            try:
                for t in b.meta_types:
                    if t not in mt: mt.append(t)
            except: pass
        mt.sort()
        self.meta_types=tuple(mt)
        
        default__class_init__(self)

    def all_meta_types(self):
        pmt=()
        if hasattr(self, '_product_meta_types'): pmt=self._product_meta_types
        elif hasattr(self, 'aq_acquire'):
            try: pmt=self.aq_acquire('_product_meta_types')
            except:  pass
        return self.meta_types+self.dynamic_meta_types+pmt

    def _checkId(self,id):

        if not id: raise 'Bad Request', 'No <em>id</em> was specified'

        if quote(id) != id: raise 'Bad Request', (
            """The id <em>%s<em>  is invalid - it
               contains characters illegal in URLs.""" % id)

        if id[:1]=='_': raise 'Bad Request', (
            """The id <em>%s<em>  is invalid - it 
               begins with an underscore character, _.""" % id)

        try: self=self.aq_base
        except: return

        if hasattr(self,id): raise 'Bad Request', (
            """The id <em>%s<em>  is invalid - it
               is already in use.""" % id)

    def _checkObject(self, object):
        t=object.meta_type
        if callable(t): t=t()
        for d in self.all_meta_types():
            if d['name']==t: return
        raise 'Bad Request', 'Object type is not supported'

    def parentObject(self):
        try:
            if self.aq_parent.isAnObjectManager:
                return (self.aq_parent,)
        except: pass
        return ()

    def _setObject(self,id,object,roles=None,user=None):
        self._checkId(id)
        setattr(self,id,object)
        try:    t=object.meta_type
        except: t=None
        self._objects=self._objects+({'id':id,'meta_type':t},)

        # This is a nasty hack that provides a workaround for any
        # existing customers with the acl_users/__allow_groups__
        # bug. Basically when you add an object, we'll do the check
        # an make the fix if necessary.
        have=self.__dict__.has_key
        if have('__allow_groups__') and (not have('acl_users')):
            delattr(self, '__allow_groups__')



    def _delObject(self,id):
        delattr(self,id)
        if id=='acl_users':
            # Yikes - acl_users is referred to by two names and
            # must be treated as a special case!
            try:    delattr(self, '__allow_groups__')
            except: pass
        self._objects=tuple(filter(lambda i,n=id: i['id']!=n, self._objects))

    def objectIds(self, spec=None):
        """Return a list of subobject ids.

        Returns a list of subobject ids of the current object.  If 'spec' is
        specified, returns objects whose meta_type matches 'spec'.
        """
        if spec is not None:
            if type(spec)==type('s'):
                spec=[spec]
            set=[]
            for ob in self._objects:
                if ob['meta_type'] in spec:
                    set.append(ob['id'])
            return set
        return map(lambda i: i['id'], self._objects)

    def objectValues(self, spec=None):
        """Return a list of the actual subobjects.

        Returns a list of actual subobjects of the current object.  If
        'spec' is specified, returns only objects whose meta_type match 'spec'
        """
        if spec is not None:
            if type(spec)==type('s'):
                spec=[spec]
            set=[]
            for ob in self._objects:
                if ob['meta_type'] in spec:
                    set.append(getattr(self, ob['id']))
            return set
        return map(lambda i,s=self: getattr(s,i['id']), self._objects)

    def objectItems(self, spec=None):
        """Return a list of (id, subobject) tuples.

        Returns a list of (id, subobject) tuples of the current object.
        If 'spec' is specified, returns only objects whose meta_type match
        'spec'
        """
        if spec is not None:
            if type(spec)==type('s'):
                spec=[spec]
            set=[]
            for ob in self._objects:
                if ob['meta_type'] in spec:
                    set.append((ob['id'], getattr(self, ob['id'])))
            return set
        return map(lambda i,s=self: (i['id'], getattr(s,i['id'])),
                                    self._objects)
    def objectMap(self):
        # Return a tuple of mappings containing subobject meta-data
        return self._objects

    def objectIds_d(self,t=None):
        v=self.objectIds(t)
        try:    n=self._reserved_names
        except: return v
        return filter(lambda x,r=n: x not in r, v)

    def objectValues_d(self,t=None):
        v=self.objectIds(t)
        try:    n=self._reserved_names
        except: return map(lambda i,s=self: getattr(s,i), v)
        return map(lambda i,s=self: getattr(s,i),
                    filter(lambda x,r=n: x not in r, v))

    def objectItems_d(self,t=None):
        v=self.objectItems(t)
        try:    n=self._reserved_names
        except: return v
        return filter(lambda x,r=n: x[0] not in r, v)

    def objectMap_d(self,t=None):
        v=self._objects
        try:    n=self._reserved_names
        except: return v
        return filter(lambda x,r=n: x['id'] not in r, v)

    def superIds(self,t):
        if type(t)==type('s'): t=(t,)
        obj=self
        vals=[]
        x=0
        while x < 100:
            try:    set=obj._objects
            except: set=()
            for i in set:
                try:
                    if i['meta_type'] in t:
                        id=i['id']
                        if not id in vals: vals.append(id)
                except: pass
            try:    obj=obj.aq_parent
            except: return vals
            x=x+1
        return vals

    def superValues(self,t):
        if type(t)==type('s'): t=(t,)
        obj=self
        seen={}
        vals=[]
        have=seen.has_key
        x=0
        while x < 100:
            try:    set=obj._objects
            except: set=()
            for i in set:
                try:
                    id=i['id']
                    if (not have(id)) and (i['meta_type'] in t):
                        vals.append(getattr(obj,id))
                        seen[id]=1
                except: pass
            try:    obj=obj.aq_parent
            except: return vals
            x=x+1
        return vals

    def superItems(self,t):
        if type(t)==type('s'): t=(t,)
        obj=self
        seen={}
        vals=[]
        have=seen.has_key
        x=0
        while x < 100:
            try:    set=obj._objects
            except: set=()
            for i in set:
                try:
                    id=i['id']
                    if (not have(id)) and (i['meta_type'] in t):
                        vals.append((id,getattr(obj,id),))
                        seen[id]=1
                except: pass
            try:    obj=obj.aq_parent
            except: return vals
            x=x+1
        return vals

    def superHasAttr(self,attr):
        obj=self
        seen={}
        vals=[]
        have=seen.has_key
        x=0
        while x < 100:
            try:    set=obj._objects
            except: set=()
            for i in set:
                try:
                    id=i['id']
                    if not have(id):
                        v=getattr(obj,id)
                        if hasattr(v,attr):
                            vals.append(v)
                            seen[id]=1
                except: pass
            try:    obj=obj.aq_parent
            except: return vals
            x=x+1
        return vals


    manage_addProduct=App.FactoryDispatcher.ProductDispatcher()


    def manage_delObjects(self, ids=[], REQUEST=None):
        """Delete a subordinate object
        
        The objects specified in 'ids' get deleted.
        """
        if type(ids) is type(''): ids=[ids]
        if not ids:
            return MessageDialog(title='No items specified',
                   message='No items were specified!',
                   action ='./manage_main',)
        try:    p=self._reserved_names
        except: p=()
        for n in ids:
            if n in p:
                return MessageDialog(title='Not Deletable',
                       message='<EM>%s</EM> cannot be deleted.' % n,
                       action ='./manage_main',)
        while ids:
            id=ids[-1]
            if not hasattr(self, id) or not self.__dict__.has_key(id):
                raise 'BadRequest', '%s does not exist' % ids[-1]
            self._delObject(id)
            del ids[-1]
        if REQUEST is not None:
                return self.manage_main(self, REQUEST, update_menu=1)


    def _setProperty(self,id,value,type='string'):
        self._checkId(id)
        self._properties=self._properties+({'id':id,'type':type},)
        setattr(self,id,value)

    def _delProperty(self,id):
        delattr(self,id)
        self._properties=tuple(filter(lambda i, n=id: i['id'] != n,
                                     self._properties))
    def propertyIds(self):
        """ Return a list of property ids """
        return map(lambda i: i['id'], self._properties)

    def propertyValues(self):
        """ Return a list of actual property objects """
        return map(lambda i,s=self: getattr(s,i['id']), self._properties)

    def propertyItems(self):
        """ Return a list of (id,property) tuples """
        return map(lambda i,s=self: (i['id'],getattr(s,i['id'])), 
                                    self._properties)
    def propertyMap(self):
        """ Return a tuple of mappings, giving meta-data for properties """
        return self._properties

    def propertyMap_d(self):
        v=self._properties
        try:    n=self._reserved_names
        except: return v
        return filter(lambda x,r=n: x['id'] not in r, v)

    def manage_addProperty(self,id,value,type,REQUEST=None):
        """Add a new property (www)

        Sets a new property with id, type, and value.
        """
        try:    value=type_converters[type](value)
        except: pass
        self._setProperty(id,value,type)
        if REQUEST is not None:
            return self.manage_propertiesForm(self, REQUEST)

    def manage_editProperties(self,REQUEST):
        """Edit object properties"""
        for p in self._properties:
            n=p['id']
            try:    setattr(self,n,REQUEST[n])
            except: setattr(self,n,'')
        return MessageDialog(
               title  ='Success!',
               message='Your changes have been saved',
               action ='manage_propertiesForm')

    def manage_changeProperties(self, REQUEST=None, **kw):
        """Change existing object properties.

        Change object properties by passing either a mapping object
        of name:value pairs {'foo':6} or passing name=value parameters
        """
        if REQUEST is None:
            props={}
        else:
            props=REQUEST

        if kw:
            for name, value in kw.items():
                props[name]=value

        for name, value in props.items():
            if self.hasProperty(name):
                setattr(self, name, value)
    
        if REQUEST is not None:
            return MessageDialog(
                title  ='Success!',
                message='Your changes have been saved',
                action ='manage_propertiesForm')

    def hasProperty(self, id):
        """returns 1 if object has a settable property 'id'"""
        for p in self._properties:
            if id == p['id']: return 1
        return 0

    def manage_delProperties(self,ids,REQUEST=None):
        """Delete one or more properties

        Deletes properties specified by 'ids'
        """
        try:    p=self._reserved_names
        except: p=()
        if ids is None:
            return MessageDialog(title='No property specified',
                   message='No properties were specified!',
                   action ='./manage_propertiesForm',)
        for n in ids:
            if n in p:
                return MessageDialog(
                title  ='Cannot delete %s' % n,
                message='The property <I>%s</I> cannot be deleted.' % n,
                action ='manage_propertiesForm')
            try:    self._delProperty(n)
            except: raise 'BadRequest', (
                          'The property <I>%s</I> does not exist' % n)
        if REQUEST is not None:
            return self.manage_propertiesForm(self, REQUEST)


    def _defaultInput(self,n,t,v):
        return '<INPUT NAME="%s:%s" SIZE="40" VALUE="%s"></TD>' % (n,t,v)

    def _stringInput(self,n,t,v):
        return ('<INPUT NAME="%s:%s" SIZE="40" VALUE="%s"></TD>'
                % (n,t,html_quote(v)))

    def _booleanInput(self,n,t,v):
        if v: v="CHECKED"
        else: v=''
        return ('<INPUT TYPE="CHECKBOX" NAME="%s:%s" SIZE="50" %s></TD>'
                % (n,t,v))

    def _selectInput(self,n,t,v):
        s=['<SELECT NAME="%s:%s">' % (n,t)]
        map(lambda i: s.append('<OPTION>%s' % i), v)
        s.append('</SELECT>')
        return join(s,'\n')

    def _linesInput(self,n,t,v):
        try: v=html_quote(join(v,'\n'))
        except: v=''
        return (
        '<TEXTAREA NAME="%s:lines" ROWS="10" COLS="40">%s</TEXTAREA>'
        % (n,v))

    def _tokensInput(self,n,t,v):
        try: v=html_quote(join(v,' '))
        except: v=''
        return ('<INPUT NAME="%s:%s" SIZE="40" VALUE="%s"></TD>'
                % (n,t,html_quote(v)))

    def _textInput(self,n,t,v):
        return ('<TEXTAREA NAME="%s:text" ROWS="10" COLS="40">%s</TEXTAREA>'
                % (n,html_quote(v)))

    _inputMap={
        'float':        _defaultInput,
        'int':          _defaultInput,
        'long':         _defaultInput,
        'string':       _stringInput,
        'lines':        _linesInput,
        'text':         _textInput,
        'date':         _defaultInput,
        'tokens':       _tokensInput,   
#       'boolean':      _booleanInput,  
        }

    propertyTypes=map(lambda key: (lower(key), key), _inputMap.keys())
    propertyTypes.sort()
    propertyTypes=map(lambda key:
                      {'id': key[1],
                       'selected': key[1]=='string' and 'SELECTED' or ''},
                      propertyTypes)
                      

    def propertyInputs(self):
        imap=self._inputMap
        r=[]
        for p in self._properties:
            n=p['id']
            t=p['type']
            v=getattr(self,n)
            r.append({'id': n, 'input': imap[t](None,n,t,v)})
        return r
