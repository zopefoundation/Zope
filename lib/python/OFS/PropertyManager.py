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

"""Property management"""
__version__='$Revision: 1.2 $'[11:-2]



## from ObjectManager import ObjectManager
## from CopySupport import CopyContainer
## from FindSupport import FindSupport
## from Image import Image, File
## from Document import DocumentHandler
## from AccessControl.Role import RoleManager
## import SimpleItem
## from string import rfind, lower
## from content_types import content_type, find_binary, text_type
## import Globals

from ZPublisher.Converters import type_converters
from Globals import HTMLFile, MessageDialog
from string import find,join,lower,split
from DocumentTemplate import html_quote
from DateTime import DateTime



def aq_base(ob):
    if hasattr(ob, 'aq_base'):
        return ob.aq_base
    return ob


class PropertyManager:
    """
    The PropertyManager mixin class provides an object with
    transparent property management. An object which wants to
    have properties should inherit from PropertyManager.

    An object which inherits from PropertyManager should include
    the following entry in its manage_options structure:

    {'label':'Properties', 'action':'manage_propertiesForm',}

    An object which inherits from PropertyManager should also
    include the following entry in its __ac_permissions__
    structure:

    ('Manage properties', ('manage_addProperty',
                           'manage_editProperties',
                           'manage_delProperties',
                           'manage_changeProperties',)),
    """
    manage_propertiesForm=HTMLFile('properties', globals())

    _properties=({'id':'title', 'type': 'string'},)
    _reserved_names=()

    def valid_property_id(self, id):
        if not id or id[:1]=='_' or hasattr(aq_base(self), id):
            return 0
        return 1

    def getProperty(self, id, d=None):
        """Get the property 'id', returning the optional second 
           argument or None if no such property is found."""
        if self.hasProperty(id):
            return getattr(self, id)
        return d
        
    def _setProperty(self, id, value, type='string'):
        if not self.valid_property_id(id):
            raise 'Bad Request', 'Invalid property id'
        self._properties=self._properties+({'id':id,'type':type},)
        setattr(self,id,value)

    def hasProperty(self, id):
        """Return true if object has a property 'id'"""
        for p in self._properties:
            if id==p['id']:
                return 1
        return 0

    def _delProperty(self, id):
        if not self.hasProperty(id):
            raise ValueError, 'The property %s does not exist' % id
        delattr(self,id)
        self._properties=tuple(filter(lambda i, n=id: i['id'] != n,
                                      self._properties))

    def propertyIds(self):
        """Return a list of property ids """
        return map(lambda i: i['id'], self._properties)

    def propertyValues(self):
        """Return a list of actual property objects """
        return map(lambda i,s=self: getattr(s,i['id']), self._properties)

    def propertyItems(self):
        """Return a list of (id,property) tuples """
        return map(lambda i,s=self: (i['id'],getattr(s,i['id'])), 
                                    self._properties)
    def propertyMap(self):
        """Return a tuple of mappings, giving meta-data for properties """
        return self._properties

    def propertyMap_d(self):
        v=self._properties
        try:    n=self._reserved_names
        except: return v
        return filter(lambda x,r=n: x['id'] not in r, v)

    # Web interface
    
    def manage_addProperty(self, id, value, type, REQUEST=None):
        """Add a new property via the web. Sets a new property with
           the given id, type, and value."""
        if type_converters.has_key(type):
            value=type_converters[type](value)
        self._setProperty(id, value, type)
        if REQUEST is not None:
            return self.manage_propertiesForm(self, REQUEST)

    def manage_editProperties(self, REQUEST):
        """Edit object properties via the web."""
        for p in self._properties:
            n=p['id']
            setattr(self, n, REQUEST.get(n, ''))
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



    def manage_delProperties(self, ids=None, REQUEST=None):
        """Delete one or more properties

        Deletes properties specified by 'ids'
        """
        if ids is None:
            return MessageDialog(
                   title='No property specified',
                   message='No properties were specified!',
                   action ='./manage_propertiesForm',)
        rnames=self._reserved_names
        for n in ids:
            if n in rnames:
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
