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

"""Property sheets"""
__version__='$Revision: 1.9 $'[11:-2]

import time, string, App.Management
from ZPublisher.Converters import type_converters
from Globals import HTMLFile, MessageDialog
from string import find,join,lower,split,rfind
from Acquisition import Implicit, Explicit
from ExtensionClass import Base
from Globals import Persistent

class View(App.Management.Tabs):
    """A view of an object, typically used for management purposes
    """

    def manage_options(self):
        """Return a manage option data structure for me instance
        """
        try: r=self.REQUEST
        except: r=None
        if r is None: pre='../../'
        else:
            pre=r['URL']
            for i in (1,2,3):
                l=rfind(pre,'/')
                if l >= 0:
                    pre=pre[:l]
            pre=pre+'/'
            
        r=[]
        for d in self.aq_parent.aq_parent.manage_options:
            r.append({'label': d['label'],
                      'action': pre+d['action']+'/index_html'})
        return r

    def tabs_path_info(self, script, path):
        l=rfind(path,'/')
        if l >= 0: path=path[:l]
        return PropertySheet.inheritedAttribute('tabs_path_info')(
            self, script, path)


class PropertySheet(Persistent, Implicit):
    """A PropertySheet is a container for a set of related properties and
       metadata describing those properties. PropertySheets may or may not
       provide a web interface for managing its properties."""

    _properties=()

    def __init__(self, id, md=None):
        # Create a new property set, using the given id and namespace
        # string. The namespace string should be usable as an xml name-
        # space identifier.
        self.id=id
        self.md=md or {}
        
    def xml_namespace(self):
        # Return a namespace string usable as an xml namespace
        # for this property set.
        return self.md.get('xmlns', '')

    def v_self(self):
        return self

    def valid_property_id(self, id):
        # Return a true value if the given id is valid to use as 
        # a property id. Note that this method does not consider 
        # factors other than the actual value of the id, such as 
        # whether the given id is already in use.
        if not id or (id[:1]=='_') or (' ' in id):
            return 0
        return 1

    def hasProperty(self, id):
        # Return a true value if a property exists with the given id.
        for prop in self.propertyMap():
            if id==prop['id']:
                return 1
        return 0

    def getProperty(self, id, default=None):
        # Return the property with the given id, returning the optional
        # second argument or None if no such property is found.
        if self.hasProperty(id):
            return getattr(self.v_self(), id)
        return default

    def _setProperty(self, id, value, type='string', meta=None):
        # Set a new property with the given id, value and optional type.
        # Note that different property sets may support different typing
        # systems.
        if not self.valid_property_id(id):
            raise 'Bad Request', 'Invalid property id.'
        self=self.v_self()
        if meta is None: meta={}
        prop={'id':id, 'type':type, 'meta':meta}
        self._properties=self._properties+(prop,)
        setattr(self, id, value)

    def _updateProperty(self, id, value, meta=None):
        # Update the value of an existing property. If value is a string,
        # an attempt will be made to convert the value to the type of the
        # existing property. If a mapping containing meta-data is passed,
        # it will used to _replace_ the properties meta data.
        if not self.hasProperty(id):
            raise 'Bad Request', 'The property %s does not exist.' % id
        if type(value)==type(''):
            proptype=self.propertyInfo(id).get('type', 'string')
            if type_converters.has_key(proptype):
                value=type_converters[proptype](value)
        if meta is not None:
            props=[]
            for prop in self.v_self()._properties:
                if prop['id']==id: prop['meta']=meta
                props.append(prop)
            self.v_self()._properties=props
        setattr(self.v_self(), id, value)

    def _delProperty(self, id):
        # Delete the property with the given id. If a property with the
        # given id does not exist, a ValueError is raised.
        if not self.hasProperty(id):
            raise ValueError, 'The property %s does not exist.' % id
        self=self.v_self()
        delattr(self, id)
        self._properties=tuple(filter(lambda i, n=id: i['id'] != n,
                                      self._properties))

    def propertyIds(self):
        # Return a list of property ids.
        return map(lambda i: i['id'], self.propertyMap())

    def propertyValues(self):
        # Return a list of property values.
        return map(lambda i, s=self: s.getProperty(i['id']),
                   self.propertyMap())

    def propertyItems(self):
        # Return a list of (id, property) tuples.
        return map(lambda i, s=self: (i['id'], s.getProperty(i['id'])), 
                   self.propertyMap())

    def propertyInfo(self, id):
        # Return a mapping containing property meta-data
        for p in self.propertyMap():
            if p['id']==id: return p
        raise ValueError, 'Property %s not found.' % id

    def propertyMap(self):
        # Return a tuple of mappings, giving meta-data for properties.
        return self.v_self()._properties

    def propdict(self):
        dict={}
        for p in self.propertyMap():
            dict[p['id']]=p
        return dict

    def dav__propstat(self, allprop, names, join=string.join):
        # The dav__propstat method returns a chunk of xml containing
        # one or more propstat elements indicating property names,
        # values, errors and status codes. This is called by some
        # of the WebDAV support machinery. If a property set does
        # not support WebDAV, this method should return an empty
        # string.
        propstat='<d:propstat xmlns:ps="%s">\n' \
                 '  <d:prop>\n' \
                 '%%s\n' \
                 '  </d:prop>\n' \
                 '  <d:status>HTTP/1.1 %%s</d:status>\n%%s' \
                 '</d:propstat>\n' % self.xml_namespace()
        errormsg='  <d:responsedescription>%s</d:responsedescription>\n'
        result=[]
        if not allprop and not names:
            # propname request
            for name in self.propertyIds():
                result.append('  <ps:%s/>' % name)
            if not result: return ''
            result=join(result, '\n')
            return propstat % (result, '200 OK', '')
        elif allprop:
            for item in self.propertyMap():
                name, type=item['id'], item.get('type','string')
                meta=item.get('meta', {})
                value=self.getProperty(name)
                if type=='tokens':
                    value=join(value, ' ')
                elif type=='lines':
                    value=join(value, '\n')
                if meta.get('dav_xml', 0):
                    prop=value
                else: prop='  <ps:%s>%s</ps:%s>' % (name, value, name)
                result.append(prop)
            if not result: return ''
            result=join(result, '\n')
            return propstat % (result, '200 OK', '')
        else:
            propdict=self.propdict()
            xml_id=self.xml_namespace()
            for name, ns in names:
                if ns==xml_id:
                    if not propdict.has_key(name):
                        prop='  <ps:%s/>' % name
                        emsg=errormsg % 'No such property: %s' % name
                        result.append(propstat % (prop, '404 Not Found', emsg))
                    else:
                        item=propdict[name]
                        name, type=item['id'], item.get('type','string')
                        meta=item.get('meta', {})
                        value=self.getProperty(name)
                        if type=='tokens':
                            value=join(value, ' ')
                        elif type=='lines':
                            value=join(value, '\n')
                        if meta.get('dav_xml', 0):
                            prop=value
                        else:
                            prop='  <ps:%s>%s</ps:%s>' % (name, value, name)
                        result.append(propstat % (prop, '200 OK', ''))
            if not result: return ''
            return join(result, '')

    # Web interface
    
    manage_propertiesForm=HTMLFile('properties', globals())
    
    def manage_addProperty(self, id, value, type, REQUEST=None):
        """Add a new property via the web. Sets a new property with
        the given id, type, and value."""
        if type_converters.has_key(type):
            value=type_converters[type](value)
        self._setProperty(id, value, type)
        if REQUEST is not None:
            return self.manage_propertiesForm(self, REQUEST)

    def manage_changeProperties(self, REQUEST=None, **kw):
        """Change existing object properties by passing either a mapping
           object of name:value pairs {'foo':6} or passing name=value
           parameters."""
        if REQUEST is None: props={}
        else: props=REQUEST
        if kw:
            for name, value in kw.items():
                props[name]=value
        propdict=self.propdict()
        vself=self.v_self()
        for name, value in props.items():
            if self.hasProperty(name):
                if not 'w' in propdict[name].get('mode', 'wd'):
                    raise 'BadRequest', '%s cannot be changed.' % name
                vself._updateProperty(name, value)
        if REQUEST is not None:
            return MessageDialog(
                title  ='Success!',
                message='Your changes have been saved.',
                action ='manage_propertiesForm')

    def manage_delProperties(self, ids=None, REQUEST=None):
        """Delete one or more properties specified by 'ids'."""
        if ids is None:
            return MessageDialog(
                   title='No property specified',
                   message='No properties were specified!',
                   action ='./manage_propertiesForm',)
        propdict=self.propdict()
        vself=self.v_self()
        if hasattr(vself, '_reserved_names'):
            nd=vself._reserved_names
        else: nd=()
        for id in ids:
            if not propdict.has_key(id):
                raise 'BadRequest', (
                      'The property <em>%s</em> does not exist.' % id)
            if (not 'd' in propdict[id].get('mode', 'wd')) or (id in nd):
                return MessageDialog(
                title  ='Cannot delete %s' % id,
                message='The property <em>%s</em> cannot be deleted.' % id,
                action ='manage_propertiesForm')
            self._delProperty(id)
        if REQUEST is not None:
            return self.manage_propertiesForm(self, REQUEST)


class Virtual:

    def __init__(self):
        pass
    
    def v_self(self):
        return self.aq_parent.aq_parent

class DefaultProperties(Virtual, PropertySheet):
    """The default property set mimics the behavior of old-style Zope
       properties -- it stores its property values in the instance of
       its owner."""

    id='default'
    md={'xmlns': 'http://www.zope.org/propsets/default'}


class DAVProperties(Virtual, PropertySheet):
    """WebDAV properties"""

    id='webdav'
    md={'xmlns': 'DAV:'}
    pm=({'id':'creationdate',     'mode':'r'},
        {'id':'displayname',      'mode':'r'},
        {'id':'resourcetype',     'mode':'r'},
        {'id':'getlastmodified',  'mode':'r'},
        {'id':'getcontenttype',   'mode':'r'},
        {'id':'getcontentlength', 'mode':'r'},
        {'id':'source',           'mode':'r'},
        )

    def getProperty(self, id, default=None):
        method='dav__%s' % id
        if not hasattr(self, method):
            return default
        return getattr(self, method)()

    def _setProperty(self, id, value, type='string', meta=None):
        raise ValueError, '%s cannot be set.' % id

    def _updateProperty(self, id, value):
        raise ValueError, '%s cannot be updated.' % id

    def _delProperty(self, id):
        raise ValueError, '%s cannot be deleted.' % id

    def propertyMap(self):
        return self.pm
    
    def dav__creationdate(self):
        return ''

    def dav__displayname(self):
        return absattr(self.v_self().id)

    def dav__resourcetype(self):
        self=self.v_self()
        if hasattr(aq_base(self), 'isAnObjectManager') and \
           self.isAnObjectManager:
            return '<d:collection/>'
        return ''

    def dav__getlastmodified(self):
        self=self.v_self()
        if hasattr(self, '_p_mtime'):
            return rfc1123_date(self._p_mtime)
        return ''

    def dav__getcontenttype(self):
        self=self.v_self()
        if hasattr(self, 'content_type'):
            return self.content_type
        return ''

    def dav__getcontentlength(self):
        self=self.v_self()
        if hasattr(self, 'get_size'):
            return self.get_size()
        return ''

    def dav__source(self):
        self=self.v_self()
        if hasattr(self, 'meta_type') and self.meta_type in \
           ('Document','DTMLDocument','DTMLMethod','ZSQLMethod'):
            url=self.absolute_url()
            return '<d:src>%s</d:src>\n' \
                   '<d:dst>%s/object_src</d:dst>' % (url, url)
        return ''

    def dav__supportedlock(self):
        return '<d:supportedlock>\n' \
               '<d:lockentry>\n' \
               '<d:lockscope><d:exclusive/></d:lockscope>\n' \
               '<d:locktype><d:write/></d:locktype>\n' \
               '</d:lockentry>\n' \
               '</d:supportedlock>\n'

    def dav__lockdiscovery(self):
        text=['<d:lockdiscovery>\n']
        for lock in self.dav__get_locks():
            txt='<d:activelock>\n' \
            '<d:locktype><d:%(type)s/></d:locktype>\n' \
            '<d:lockscope><d:%(scope)s/></d:lockscope>\n' \
            '<d:depth>%(depth)s</d:depth>\n' \
            '<d:owner>%(owner)s</d:owner>\n' \
            '<d:timeout>%(timeout)s</d:timeout>\n' \
            '<d:locktoken>\n' \
            '<d:href>opaquelocktoken:%(token)s</d:href>\n' \
            '</d:locktoken>\n' \
            '</d:activelock>\n' % lock.__dict__
            text.append(lock.dav__activelock())
        text.append('</d:lockdiscovery>\n')
        return string.join(text, '')


class PropertySheets(Implicit):
    """A tricky container to keep property sets from polluting
       an object's direct attribute namespace."""
    
    id='propertysheets'

    default=DefaultProperties()
    webdav =DAVProperties()

    def __init__(self, parent=None):
        pass

    def __propsets__(self):
        propsets=self.aq_parent.__propsets__
        return (self.default, self.webdav) + propsets

    def __bobo_traverse__(self, REQUEST, name=None):
        for propset in self.__propsets__():
            if propset.id==name:
                return propset.__of__(self)
        return getattr(self, name)

    def __getitem__(self, n):
        return self.__propsets__()[n].__of__(self)

    def items(self):
        propsets=self.__propsets__()
        return map(lambda n, s=self: n.__of__(s), propsets)
        
    def get(self, name, default=None):
        for propset in self.__propsets__():
            if propset.id==name or propset.xml_namespace()==name:
                return propset.__of__(self)
        return default

    def manage_addPropertySheet(self, id, ns):
        """ """
        md={'xmlns':ns}
        ps=PropertySheet(id, md)
        self.addPropertySheet(ps)
        return 'OK'

    def addPropertySheet(self, propset):
        propsets=self.aq_parent.__propsets__
        propsets=propsets+(propset,)
        self.aq_parent.__propsets__=propsets

    def delPropertySheet(self, name):
        result=[]
        for propset in self.aq_parent.__propsets__:
            if propset.id != name and  propset.xml_namespace() != name:
                result.append(propset)
        self.aq_parent.__propsets__=tuple(result)

    def __len__(self):
        return len(self.__propsets__())



class vps(Base):
    # The vps object implements a "computed attribute" - it ensures
    # that a PropertySheets instance is returned when the propertysheets
    # attribute of a PropertyManager is accessed.
    def __init__(self, c=PropertySheets):
        self.c=c
        
    def __of__(self, parent):
        if hasattr(parent, 'aq_base'):
            parent=parent.aq_base
        return self.c(parent)



def absattr(attr):
    if callable(attr):
        return attr()
    return attr

def aq_base(ob):
    if hasattr(ob, 'aq_base'):
        return ob.aq_base
    return ob

def rfc1123_date(ts=None):
    # Return an RFC 1123 format date string, required for
    # use in HTTP Date headers per the HTTP 1.1 spec.
    if ts is None: ts=time.time()
    ts=time.asctime(time.gmtime(ts))
    ts=string.split(ts)
    return '%s, %s %s %s %s GMT' % (ts[0],ts[2],ts[1],ts[3],ts[4])
