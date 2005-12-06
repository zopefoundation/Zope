##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Property management

$Id$
"""

from cgi import escape
from types import ListType

import ExtensionClass, Globals
from Acquisition import aq_base
from Globals import DTMLFile, MessageDialog
from Globals import Persistent
from zExceptions import BadRequest
from zope.interface import implements
from ZPublisher.Converters import type_converters

import ZDOM
from interfaces import IPropertyManager
from PropertySheets import DefaultPropertySheets, vps


class PropertyManager(ExtensionClass.Base, ZDOM.ElementWithAttributes):

    """
    The PropertyManager mixin class provides an object with
    transparent property management. An object which wants to
    have properties should inherit from PropertyManager.

    An object may specify that it has one or more predefined
    properties, by specifying an _properties structure in its
    class::

      _properties=({'id':'title', 'type': 'string', 'mode': 'w'},
                   {'id':'color', 'type': 'string', 'mode': 'w'},
                   )

    The _properties structure is a sequence of dictionaries, where
    each dictionary represents a predefined property. Note that if a
    predefined property is defined in the _properties structure, you
    must provide an attribute with that name in your class or instance
    that contains the default value of the predefined property.

    Each entry in the _properties structure must have at least an 'id'
    and a 'type' key. The 'id' key contains the name of the property,
    and the 'type' key contains a string representing the object's type.
    The 'type' string must be one of the values: 'float', 'int', 'long',
    'string', 'lines', 'text', 'date', 'tokens', 'selection', or
    'multiple section'.

    For 'selection' and 'multiple selection' properties, there is an
    addition item in the property dictionay, 'select_variable' which
    provides the name of a property or method which returns a list of
    strings from which the selection(s) can be chosen.

    Each entry in the _properties structure may *optionally* provide a
    'mode' key, which specifies the mutability of the property. The 'mode'
    string, if present, must contain 0 or more characters from the set
    'w','d'.

    A 'w' present in the mode string indicates that the value of the
    property may be changed by the user. A 'd' indicates that the user
    can delete the property. An empty mode string indicates that the
    property and its value may be shown in property listings, but that
    it is read-only and may not be deleted.

    Entries in the _properties structure which do not have a 'mode' key
    are assumed to have the mode 'wd' (writeable and deleteable).

    To fully support property management, including the system-provided
    tabs and user interfaces for working with properties, an object which
    inherits from PropertyManager should include the following entry in
    its manage_options structure::

      {'label':'Properties', 'action':'manage_propertiesForm',}

    to ensure that a 'Properties' tab is displayed in its management
    interface. Objects that inherit from PropertyManager should also
    include the following entry in its __ac_permissions__ structure::

      ('Manage properties', ('manage_addProperty',
                             'manage_editProperties',
                             'manage_delProperties',
                             'manage_changeProperties',)),
    """

    implements(IPropertyManager)

    manage_options=(
        {'label':'Properties', 'action':'manage_propertiesForm',
         'help':('OFSP','Properties.stx')},
        )

    manage_propertiesForm=DTMLFile('dtml/properties', globals(),
                                   property_extensible_schema__=1)
    manage_propertyTypeForm=DTMLFile('dtml/propertyType', globals())

    title=''
    _properties=({'id':'title', 'type': 'string', 'mode':'wd'},)
    _reserved_names=()

    __ac_permissions__=(
        ('Manage properties', ('manage_addProperty',
                               'manage_editProperties',
                               'manage_delProperties',
                               'manage_changeProperties',
                               'manage_propertiesForm',
                               'manage_propertyTypeForm',
                               'manage_changePropertyTypes',
                               )),
        ('Access contents information',
         ('hasProperty', 'propertyIds', 'propertyValues','propertyItems',
          'getProperty', 'getPropertyType', 'propertyMap', ''),
         ('Anonymous', 'Manager'),
         ),
        )

    __propsets__=()
    propertysheets=vps(DefaultPropertySheets)

    def valid_property_id(self, id):
        if not id or id[:1]=='_' or (id[:3]=='aq_') \
           or (' ' in id) or hasattr(aq_base(self), id) or escape(id) != id:
            return 0
        return 1

    def hasProperty(self, id):
        """Return true if object has a property 'id'.
        """
        for p in self._properties:
            if id==p['id']:
                return 1
        return 0

    def getProperty(self, id, d=None):
        """Get the property 'id'.

        Returns the optional second argument or None if no such property is
        found.
        """
        if self.hasProperty(id):
            return getattr(self, id)
        return d

    def getPropertyType(self, id):
        """Get the type of property 'id'.

        Returns None if no such property exists.
        """
        for md in self._properties:
            if md['id']==id:
                return md.get('type', 'string')
        return None

    def _wrapperCheck(self, object):
        # Raise an error if an object is wrapped.
        if hasattr(object, 'aq_base'):
            raise ValueError, 'Invalid property value: wrapped object'
        return

    def _setPropValue(self, id, value):
        self._wrapperCheck(value)
        if type(value) == ListType:
            value = tuple(value)
        setattr(self,id,value)

    def _delPropValue(self, id):
        delattr(self,id)

    def _setProperty(self, id, value, type='string'):
        # for selection and multiple selection properties
        # the value argument indicates the select variable
        # of the property

        self._wrapperCheck(value)
        if not self.valid_property_id(id):
            raise BadRequest, 'Invalid or duplicate property id'

        if type in ('selection', 'multiple selection'):
            if not hasattr(self, value):
                raise BadRequest, 'No select variable %s' % value
            self._properties=self._properties + (
                {'id':id, 'type':type, 'select_variable':value},)
            if type=='selection':
                self._setPropValue(id, '')
            else:
                self._setPropValue(id, [])
        else:
            self._properties=self._properties+({'id':id,'type':type},)
            self._setPropValue(id, value)

    def _updateProperty(self, id, value):
        # Update the value of an existing property. If value
        # is a string, an attempt will be made to convert
        # the value to the type of the existing property.
        self._wrapperCheck(value)
        if not self.hasProperty(id):
            raise BadRequest, 'The property %s does not exist' % escape(id)
        if type(value)==type(''):
            proptype=self.getPropertyType(id) or 'string'
            if type_converters.has_key(proptype):
                value=type_converters[proptype](value)
        self._setPropValue(id, value)

    def _delProperty(self, id):
        if not self.hasProperty(id):
            raise ValueError, 'The property %s does not exist' % escape(id)
        self._delPropValue(id)
        self._properties=tuple(filter(lambda i, n=id: i['id'] != n,
                                      self._properties))

    def propertyIds(self):
        """Return a list of property ids.
        """
        return map(lambda i: i['id'], self._properties)

    def propertyValues(self):
        """Return a list of actual property objects.
        """
        return map(lambda i,s=self: getattr(s,i['id']), self._properties)

    def propertyItems(self):
        """Return a list of (id,property) tuples.
        """
        return map(lambda i,s=self: (i['id'],getattr(s,i['id'])),
                                    self._properties)
    def _propertyMap(self):
        """Return a tuple of mappings, giving meta-data for properties.
        """
        return self._properties

    def propertyMap(self):
        """Return a tuple of mappings, giving meta-data for properties.

        Return copies of the real definitions for security.
        """
        return tuple(map(lambda dict: dict.copy(), self._propertyMap()))

    def propertyLabel(self, id):
        """Return a label for the given property id
        """
        for p in self._properties:
            if p['id'] == id:
                return p.get('label', id)
        return id

    def propdict(self):
        dict={}
        for p in self._properties:
            dict[p['id']]=p
        return dict


    # Web interface

    def manage_addProperty(self, id, value, type, REQUEST=None):
        """Add a new property via the web.

        Sets a new property with the given id, type, and value.
        """
        if type_converters.has_key(type):
            value=type_converters[type](value)
        self._setProperty(id.strip(), value, type)
        if REQUEST is not None:
            return self.manage_propertiesForm(self, REQUEST)

    def manage_editProperties(self, REQUEST):
        """Edit object properties via the web.

        The purpose of this method is to change all property values,
        even those not listed in REQUEST; otherwise checkboxes that
        get turned off will be ignored.  Use manage_changeProperties()
        instead for most situations.
        """
        for prop in self._propertyMap():
            name=prop['id']
            if 'w' in prop.get('mode', 'wd'):
                if prop['type'] == 'multiple selection':
                    value=REQUEST.get(name, [])
                else:
                    value=REQUEST.get(name, '')
                self._updateProperty(name, value)
        if REQUEST:
            message="Saved changes."
            return self.manage_propertiesForm(self,REQUEST,
                                              manage_tabs_message=message)

    def manage_changeProperties(self, REQUEST=None, **kw):
        """Change existing object properties.

        Change object properties by passing either a mapping object
        of name:value pairs {'foo':6} or passing name=value parameters
        """
        if REQUEST is None:
            props={}
        else: props=REQUEST
        if kw:
            for name, value in kw.items():
                props[name]=value
        propdict=self.propdict()
        for name, value in props.items():
            if self.hasProperty(name):
                if not 'w' in propdict[name].get('mode', 'wd'):
                    raise BadRequest, '%s cannot be changed' % escape(name)
                self._updateProperty(name, value)
        if REQUEST:
            message="Saved changes."
            return self.manage_propertiesForm(self,REQUEST,
                                              manage_tabs_message=message)

    # Note - this is experimental, pending some community input.

    def manage_changePropertyTypes(self, old_ids, props, REQUEST=None):
        """Replace one set of properties with another

        Delete all properties that have ids in old_ids, then add a
        property for each item in props.  Each item has a new_id,
        new_value, and new_type.  The type of new_value should match
        new_type.
        """
        err = self.manage_delProperties(old_ids)
        if err:
            if REQUEST is not None:
                return err
            return
        for prop in props:
            self._setProperty(prop.new_id, prop.new_value, prop.new_type)
        if REQUEST is not None:
            return self.manage_propertiesForm(self, REQUEST)


    def manage_delProperties(self, ids=None, REQUEST=None):
        """Delete one or more properties specified by 'ids'."""
        if REQUEST:
            # Bugfix for property named "ids" (Casey)
            if ids == self.getProperty('ids', None): ids = None
            ids = REQUEST.get('_ids', ids)
        if ids is None:
            return MessageDialog(
                   title='No property specified',
                   message='No properties were specified!',
                   action ='./manage_propertiesForm',)
        propdict=self.propdict()
        nd=self._reserved_names
        for id in ids:
            if not hasattr(aq_base(self), id):
                raise BadRequest, (
                      'The property <em>%s</em> does not exist' % escape(id))
            if (not 'd' in propdict[id].get('mode', 'wd')) or (id in nd):
                return MessageDialog(
                title  ='Cannot delete %s' % id,
                message='The property <em>%s</em> cannot be deleted.' % escape(id),
                action ='manage_propertiesForm')
            self._delProperty(id)

        if REQUEST is not None:
            return self.manage_propertiesForm(self, REQUEST)

Globals.default__class_init__(PropertyManager)
