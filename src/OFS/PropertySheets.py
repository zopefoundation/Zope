##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Property sheets
"""

import html

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import access_contents_information
from AccessControl.Permissions import manage_properties
from AccessControl.Permissions import view_management_screens
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from Acquisition import aq_base
from Acquisition import aq_parent
from App.Management import Tabs
from App.special_dtml import DTMLFile
from ExtensionClass import Base
from OFS.Traversable import Traversable
from Persistence import Persistent
from webdav.PropertySheet import DAVPropertySheetMixin
from zExceptions import BadRequest
from ZPublisher.Converters import type_converters


class Virtual:
    """A virtual propertysheet stores it's properties in it's instance."""

    def __init__(self):
        pass

    def v_self(self):
        return aq_parent(aq_parent(self))


class View(Tabs, Base):
    """A view of an object, typically used for management purposes

    This class provides bits of management framework needed by propertysheets
    to be used as a view on an object.
    """

    def manage_workspace(self, URL1, RESPONSE):
        '''Implement a "management" interface
        '''
        RESPONSE.redirect(URL1 + '/manage')

    def tpURL(self):
        return self.getId()

    def manage_options(self):
        """Return a manage option data structure for me instance
        """
        try:
            request = self.REQUEST
        except Exception:
            request = None
        if request is None:
            pre = '../../'
        else:
            pre = request['URL']
            for i in (1, 2, 3):
                loc = pre.rfind('/')
                if loc >= 0:
                    pre = pre[:loc]
            pre = pre + '/'

        request = []
        for d in aq_parent(aq_parent(self)).manage_options:
            path = d['action']
            option = {
                'label': d['label'],
                'action': pre + path,
                'path': '../../' + path,
            }
            help = d.get('help')
            if help is not None:
                option['help'] = help
            request.append(option)
        return request

    def tabs_path_info(self, script, path):
        loc = path.rfind('/')
        if loc >= 0:
            path = path[:loc]
            loc = path.rfind('/')
            if loc >= 0:
                path = path[:loc]
        return View.inheritedAttribute('tabs_path_info')(self, script, path)

    def meta_type(self):
        try:
            return aq_parent(aq_parent(self)).meta_type
        except Exception:
            return ''


class PropertySheet(Traversable, Persistent, Implicit, DAVPropertySheetMixin):
    """A PropertySheet is a container for a set of related properties and
       metadata describing those properties. PropertySheets may or may not
       provide a web interface for managing its properties."""

    _properties = ()
    _extensible = 1

    security = ClassSecurityInfo()
    security.declareObjectProtected(access_contents_information)
    security.setPermissionDefault(access_contents_information,
                                  ('Anonymous', 'Manager'))

    __reserved_ids = ('values', 'items')

    def property_extensible_schema__(self):
        # Return a flag indicating whether new properties may be
        # added or removed.
        return self._extensible

    def __init__(self, id, md=None):
        # Create a new property set, using the given id and namespace
        # string. The namespace string should be usable as an xml name-
        # space identifier.

        if id in self.__reserved_ids:
            raise ValueError(
                "'{}' is a reserved Id (forbidden Ids are: {}) ".format(
                    id, self.__reserved_ids))

        self.id = id
        self._md = md or {}

    def getId(self):
        return self.id

    @security.protected(access_contents_information)
    def xml_namespace(self):
        """Return a namespace string usable as an xml namespace
        for this property set."""
        return self._md.get('xmlns', '')

    def v_self(self):
        return self

    def p_self(self):
        return self.v_self()

    def valid_property_id(self, id):
        if not id or id[:1] == '_' or (id[:3] == 'aq_') \
           or (' ' in id) or html.escape(id, True) != id:
            return 0
        return 1

    @security.protected(access_contents_information)
    def hasProperty(self, id):
        """Return a true value if a property exists with the given id."""
        for prop in self._propertyMap():
            if id == prop['id']:
                return 1
        return 0

    @security.protected(access_contents_information)
    def getProperty(self, id, default=None):
        # Return the property with the given id, returning the optional
        # second argument or None if no such property is found.
        if self.hasProperty(id):
            return getattr(self.v_self(), id)
        return default

    @security.protected(access_contents_information)
    def getPropertyType(self, id):
        # Get the type of property 'id', returning None if no
        # such property exists.
        pself = self.p_self()
        for md in pself._properties:
            if md['id'] == id:
                return md.get('type', 'string')
        return None

    def _wrapperCheck(self, object):
        # Raise an error if an object is wrapped.
        if hasattr(object, 'aq_base'):
            raise ValueError('Invalid property value: wrapped object')
        return

    def _setProperty(self, id, value, type='string', meta=None):
        # Set a new property with the given id, value and optional type.
        # Note that different property sets may support different typing
        # systems.
        self._wrapperCheck(value)
        if not self.valid_property_id(id):
            raise BadRequest(
                'Invalid property id, %s.' %
                html.escape(
                    id, True))

        if not self.property_extensible_schema__():
            raise BadRequest(
                'Properties cannot be added to this property sheet')
        pself = self.p_self()
        self = self.v_self()
        if hasattr(aq_base(self), id):
            if not (id == 'title' and id not in self.__dict__):
                raise BadRequest(
                    'Invalid property id, <em>%s</em>. It is in use.' %
                    html.escape(id, True))
        if meta is None:
            meta = {}
        prop = {'id': id, 'type': type, 'meta': meta}
        pself._properties = pself._properties + (prop,)
        if type in ('selection', 'multiple selection'):
            if not value:
                raise BadRequest(
                    'The value given for a new selection property '
                    'must be a variable name<p>')
            prop['select_variable'] = value
            if type == 'selection':
                value = None
            else:
                value = []

        if isinstance(value, list):
            value = tuple(value)
        setattr(self, id, value)

    def _updateProperty(self, id, value, meta=None):
        # Update the value of an existing property. If value is a string,
        # an attempt will be made to convert the value to the type of the
        # existing property. If a mapping containing meta-data is passed,
        # it will used to _replace_ the properties meta data.
        self._wrapperCheck(value)
        if not self.hasProperty(id):
            raise BadRequest('The property %s does not exist.' %
                             html.escape(id, True))
        propinfo = self.propertyInfo(id)
        if 'w' not in propinfo.get('mode', 'wd'):
            raise BadRequest('%s cannot be changed.' % html.escape(id, True))
        if isinstance(value, (str, bytes)):
            proptype = propinfo.get('type', 'string')
            if proptype in type_converters:
                value = type_converters[proptype](value)
        if meta is not None:
            props = []
            pself = self.p_self()
            for prop in pself._properties:
                if prop['id'] == id:
                    prop['meta'] = meta
                props.append(prop)
            pself._properties = tuple(props)

        if type(value) == list:
            value = tuple(value)
        setattr(self.v_self(), id, value)

    def _delProperty(self, id):
        # Delete the property with the given id. If a property with the
        # given id does not exist, a ValueError is raised.
        if not self.hasProperty(id):
            raise BadRequest('The property %s does not exist.' %
                             html.escape(id, True))
        vself = self.v_self()
        if hasattr(vself, '_reserved_names'):
            nd = vself._reserved_names
        else:
            nd = ()
        if ('d' not in self.propertyInfo(id).get('mode', 'wd')) or (id in nd):
            raise BadRequest('%s cannot be deleted.' % html.escape(id, True))
        delattr(vself, id)
        pself = self.p_self()
        pself._properties = tuple(
            [i for i in pself._properties if i['id'] != id])

    @security.protected(access_contents_information)
    def propertyIds(self):
        """Return a list of property ids."""
        return [i['id'] for i in self._propertyMap()]

    @security.protected(access_contents_information)
    def propertyValues(self):
        """Return a list of property values."""
        return [self.getProperty(i['id']) for i in self._propertyMap()]

    @security.protected(access_contents_information)
    def propertyItems(self):
        """Return a list of (id, property) tuples."""
        return [(i['id'], self.getProperty(i['id']))
                for i in self._propertyMap()]

    @security.protected(access_contents_information)
    def propertyInfo(self, id):
        """Return a mapping containing property meta-data."""
        for p in self._propertyMap():
            if p['id'] == id:
                return p
        raise ValueError(
            'The property %s does not exist.' %
            html.escape(
                id, True))

    def _propertyMap(self):
        """Return a tuple of mappings, giving meta-data for properties."""
        return self.p_self()._properties

    @security.protected(access_contents_information)
    def propertyMap(self):
        """Returns a secure copy of the property definitions."""
        return tuple(dict.copy() for dict in self._propertyMap())

    def _propdict(self):
        dict = {}
        for p in self._propertyMap():
            dict[p['id']] = p
        return dict

    manage = DTMLFile('dtml/properties', globals())

    @security.protected(manage_properties)
    def manage_propertiesForm(self, URL1, RESPONSE):
        " "
        RESPONSE.redirect(URL1 + '/manage')

    @security.protected(manage_properties)
    def manage_addProperty(self, id, value, type, REQUEST=None):
        """Add a new property via the web. Sets a new property with
        the given id, type, and value."""
        if type in type_converters:
            value = type_converters[type](value)
        self._setProperty(id, value, type)
        if REQUEST is not None:
            return self.manage(self, REQUEST)

    @security.protected(manage_properties)
    def manage_editProperties(self, REQUEST):
        """Edit object properties via the web."""
        for prop in self._propertyMap():
            name = prop['id']
            if 'w' in prop.get('mode', 'wd'):
                value = REQUEST.get(name, '')
                self._updateProperty(name, value)
        message = 'Your changes have been saved.'
        return self.manage(self, REQUEST, manage_tabs_message=message)

    @security.protected(manage_properties)
    def manage_changeProperties(self, REQUEST=None, **kw):
        """Change existing object properties.

        Change object properties by passing either a REQUEST object or
        name=value parameters
        """
        if REQUEST is None:
            props = {}
        else:
            props = REQUEST
        if kw:
            for name, value in kw.items():
                props[name] = value
        propdict = self._propdict()
        for name, value in props.items():
            if self.hasProperty(name):
                if 'w' not in propdict[name].get('mode', 'wd'):
                    raise BadRequest('%s cannot be changed' %
                                     html.escape(name, True))
                self._updateProperty(name, value)
        message = 'Your changes have been saved.'
        return self.manage(self, REQUEST, manage_tabs_message=message)

    @security.protected(manage_properties)
    def manage_delProperties(self, ids=None, REQUEST=None):
        """Delete one or more properties specified by 'ids'."""
        if REQUEST:
            # Bugfix for properties named "ids" (casey)
            if ids == self.getProperty('ids', None):
                ids = None
            ids = REQUEST.get('_ids', ids)
        if ids is None:
            raise BadRequest('No property specified')
        for id in ids:
            self._delProperty(id)
        if REQUEST is not None:
            return self.manage(self, REQUEST)


InitializeClass(PropertySheet)


class DefaultProperties(Virtual, PropertySheet, View):
    """The default property set mimics the behavior of old-style Zope
       properties -- it stores its property values in the instance of
       its owner."""

    id = 'default'
    _md = {'xmlns': 'http://www.zope.org/propsets/default'}


InitializeClass(DefaultProperties)


# import cycles
from webdav.PropertySheets import DAVProperties  # NOQA: E402 isort:skip


class PropertySheets(Traversable, Implicit, Tabs):
    """A tricky container to keep property sets from polluting
       an object's direct attribute namespace."""

    id = 'propertysheets'

    security = ClassSecurityInfo()
    security.declareObjectProtected(access_contents_information)
    security.setPermissionDefault(access_contents_information,
                                  ('Anonymous', 'Manager'))

    # optionally to be overridden by derived classes
    PropertySheetClass = PropertySheet

    webdav = DAVProperties()

    def _get_defaults(self):
        return (self.webdav,)

    def __propsets__(self):
        propsets = aq_parent(self).__propsets__
        __traceback_info__ = propsets, type(propsets)
        return self._get_defaults() + propsets

    def __bobo_traverse__(self, REQUEST, name=None):
        for propset in self.__propsets__():
            if propset.getId() == name:
                return propset.__of__(self)
        return getattr(self, name)

    def __getitem__(self, n):
        return self.__propsets__()[n].__of__(self)

    @security.protected(access_contents_information)
    def values(self):
        propsets = self.__propsets__()
        return [n.__of__(self) for n in propsets]

    @security.protected(access_contents_information)
    def items(self):
        propsets = self.__propsets__()
        r = []
        for n in propsets:
            if hasattr(n, 'id'):
                id = n.id
            else:
                id = ''
            r.append((id, n.__of__(self)))

        return r

    @security.protected(access_contents_information)
    def get(self, name, default=None):
        for propset in self.__propsets__():
            if propset.id == name or \
               getattr(propset, 'xml_namespace', object)() == name:
                return propset.__of__(self)
        return default

    @security.protected(manage_properties)
    def manage_addPropertySheet(self, id, ns, REQUEST=None):
        """ """
        md = {'xmlns': ns}
        ps = self.PropertySheetClass(id, md)
        self.addPropertySheet(ps)
        if REQUEST is None:
            return ps
        ps = self.get(id)
        REQUEST.RESPONSE.redirect('%s/manage' % ps.absolute_url())

    @security.protected(manage_properties)
    def addPropertySheet(self, propset):
        propsets = aq_parent(self).__propsets__
        propsets = propsets + (propset,)
        aq_parent(self).__propsets__ = propsets

    @security.protected(manage_properties)
    def delPropertySheet(self, name):
        result = []
        for propset in aq_parent(self).__propsets__:
            if propset.getId() != name and propset.xml_namespace() != name:
                result.append(propset)
        aq_parent(self).__propsets__ = tuple(result)

    def isDeletable(self, name):
        '''currently, we say that *name* is deletable when it is not a
        default sheet. Later, we may further restrict deletability
        based on an instance attribute.'''
        ps = self.get(name)
        if ps is None:
            return 0
        if ps in self._get_defaults():
            return 0
        return 1

    def manage_delPropertySheets(self, ids=(), REQUEST=None):
        '''delete all sheets identified by *ids*.'''
        for id in ids:
            if not self.isDeletable(id):
                raise BadRequest(
                    'attempt to delete undeletable property sheet: ' + id)
            self.delPropertySheet(id)
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect('%s/manage' % self.absolute_url())

    def __len__(self):
        return len(self.__propsets__())

    def getId(self):
        return self.id

    security.declareProtected(view_management_screens, 'manage')  # NOQA: D001
    manage = DTMLFile('dtml/propertysheets', globals())

    def manage_options(self):
        """Return a manage option data structure for me instance
        """
        try:
            request = self.REQUEST
        except Exception:
            request = None
        if request is None:
            pre = '../'
        else:
            pre = request['URLPATH0']
            for i in (1, 2):
                loc = pre.rfind('/')
                if loc >= 0:
                    pre = pre[:loc]
            pre = pre + '/'

        request = []
        for d in aq_parent(self).manage_options:
            request.append({'label': d['label'], 'action': pre + d['action']})
        return request

    def tabs_path_info(self, script, path):
        loc = path.rfind('/')
        if loc >= 0:
            path = path[:loc]
        return PropertySheets.inheritedAttribute('tabs_path_info')(
            self, script, path)


InitializeClass(PropertySheets)


class DefaultPropertySheets(PropertySheets):
    """A PropertySheets container that contains a default property
       sheet for compatibility with the arbitrary property mgmt
       design of Zope PropertyManagers."""

    default = DefaultProperties()
    webdav = DAVProperties()

    def _get_defaults(self):
        return (self.default, self.webdav)


InitializeClass(DefaultPropertySheets)


class vps(Base):
    """Virtual Propertysheets

    The vps object implements a "computed attribute" - it ensures
    that a PropertySheets instance is returned when the propertysheets
    attribute of a PropertyManager is accessed.
    """

    def __init__(self, c=PropertySheets):
        self.c = c

    def __of__(self, parent):
        return self.c().__of__(parent)
