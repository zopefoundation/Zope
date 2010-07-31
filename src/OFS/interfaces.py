##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""OFS interfaces.
"""

from zope.container.interfaces import IContainer
from zope.interface import Attribute
from zope.interface import Interface
from zope.location.interfaces import IPossibleSite
from zope.location.interfaces import IRoot
from zope.schema import Bool, BytesLine, Tuple

from AccessControl.interfaces import IOwned
from AccessControl.interfaces import IRoleManager
from Acquisition.interfaces import IAcquirer
from App.interfaces import INavigation
from App.interfaces import IUndoSupport
from persistent.interfaces import IPersistent
from webdav.interfaces import IDAVCollection
from webdav.interfaces import IDAVResource


class IOrderedContainer(Interface):

    """ Ordered Container interface.

    This interface provides a common mechanism for maintaining ordered
    collections.
    """

    def moveObjectsByDelta(ids, delta, subset_ids=None):
        """ Move specified sub-objects by delta.

        If delta is higher than the possible maximum, objects will be moved to
        the bottom. If delta is lower than the possible minimum, objects will
        be moved to the top.

        If subset_ids is not None, delta will be interpreted relative to the
        subset specified by a sequence of ids. The position of objects that
        are not part of this subset will not be changed.

        The order of the objects specified by ids will always be preserved. So
        if you don't want to change their original order, make sure the order
        of ids corresponds to their original order.

        If an object with id doesn't exist an error will be raised.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def moveObjectsUp(ids, delta=1, subset_ids=None):
        """ Move specified sub-objects up by delta in container.

        If no delta is specified, delta is 1. See moveObjectsByDelta for more
        details.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def moveObjectsDown(ids, delta=1, subset_ids=None):
        """ Move specified sub-objects down by delta in container.

        If no delta is specified, delta is 1. See moveObjectsByDelta for more
        details.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def moveObjectsToTop(ids, subset_ids=None):
        """ Move specified sub-objects to top of container.

        See moveObjectsByDelta for more details.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def moveObjectsToBottom(ids, subset_ids=None):
        """ Move specified sub-objects to bottom of container.

        See moveObjectsByDelta for more details.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def orderObjects(key, reverse=None):
        """ Order sub-objects by key and direction.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def getObjectPosition(id):
        """ Get the position of an object by its id.

        Permission -- Access contents information

        Returns -- Position
        """

    def moveObjectToPosition(id, position):
        """ Move specified object to absolute position.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on OFS.CopySupport.CopySource
class ICopySource(Interface):

    """Interface for objects which allow themselves to be copied."""

    def _canCopy(op=0):
        """Called to make sure this object is copyable.

        The op var is 0 for a copy, 1 for a move.
        """

    def _notifyOfCopyTo(container, op=0):
        """Overide this to be pickly about where you go!

        If you dont want to go there, raise an exception. The op variable is 0
        for a copy, 1 for a move.
        """

    def _getCopy(container):
        """
        """

    def _postCopy(container, op=0):
        """Called after the copy is finished to accomodate special cases.
        The op var is 0 for a copy, 1 for a move.
        """

    def _setId(id):
        """Called to set the new id of a copied object.
        """

    def cb_isCopyable():
        """Is object copyable? Returns 0 or 1
        """

    def cb_isMoveable():
        """Is object moveable? Returns 0 or 1
        """

    def cb_userHasCopyOrMovePermission():
        """
        """


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on OFS.FTPInterface.FTPInterface
class IFTPAccess(Interface):

    """Provide support for FTP access"""

    def manage_FTPstat(REQUEST):
        """Returns a stat-like tuple. (marshalled to a string) Used by
        FTP for directory listings, and MDTM and SIZE"""

    def manage_FTPlist(REQUEST):
        """Returns a directory listing consisting of a tuple of
        (id,stat) tuples, marshaled to a string. Note, the listing it
        should include '..' if there is a Folder above the current
        one.

        In the case of non-foldoid objects it should return a single
        tuple (id,stat) representing itself."""


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on OFS.Traversable.Traversable
class ITraversable(Interface):

    def absolute_url(relative=0):
        """Return the absolute URL of the object.

        This a canonical URL based on the object's physical
        containment path.  It is affected by the virtual host
        configuration, if any, and can be used by external
        agents, such as a browser, to address the object.

        If the relative argument is provided, with a true value, then
        the value of virtual_url_path() is returned.

        Some Products incorrectly use '/'+absolute_url(1) as an
        absolute-path reference.  This breaks in certain virtual
        hosting situations, and should be changed to use
        absolute_url_path() instead.
        """

    def absolute_url_path():
        """Return the path portion of the absolute URL of the object.

        This includes the leading slash, and can be used as an
        'absolute-path reference' as defined in RFC 2396.
        """

    def virtual_url_path():
        """Return a URL for the object, relative to the site root.

        If a virtual host is configured, the URL is a path relative to
        the virtual host's root object.  Otherwise, it is the physical
        path.  In either case, the URL does not begin with a slash.
        """

    def getPhysicalPath():
        """Get the physical path of the object.

        Returns a path (an immutable sequence of strings) that can be used to
        access this object again later, for example in a copy/paste operation.
        getPhysicalRoot() and getPhysicalPath() are designed to operate
        together.
        """

    def unrestrictedTraverse(path, default=None, restricted=0):
        """Lookup an object by path.

        path -- The path to the object. May be a sequence of strings or a slash
        separated string. If the path begins with an empty path element
        (i.e., an empty string or a slash) then the lookup is performed
        from the application root. Otherwise, the lookup is relative to
        self. Two dots (..) as a path element indicates an upward traversal
        to the acquisition parent.

        default -- If provided, this is the value returned if the path cannot
        be traversed for any reason (i.e., no object exists at that path or
        the object is inaccessible).

        restricted -- If false (default) then no security checking is performed.
        If true, then all of the objects along the path are validated with
        the security machinery. Usually invoked using restrictedTraverse().
        """

    def restrictedTraverse(path, default=None):
        """Trusted code traversal code, always enforces security.
        """


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on many classes
class IZopeObject(Interface):

    isPrincipiaFolderish = Bool(
        title=u"Is a folderish object",
        description=u"Should be false for simple items",
        )

    meta_type = BytesLine(
        title=u"Meta type",
        description=u"The object's Zope2 meta type",
        )


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on OFS.SimpleItem.Item and App.Management.Tabs
class IManageable(Interface):

    """Something that is manageable in the ZMI"""

    manage_tabs = Attribute("""Management tabs""")

    manage_options = Tuple(
        title=u"Manage options",
        )

    def manage(URL1):
        """Show management screen"""

    def manage_afterAdd(item, container):
        """Gets called after being added to a container"""

    def manage_beforeDelete(item, container):
        """Gets called before being deleted"""

    def manage_afterClone(item):
        """Gets called after being cloned"""

    def filtered_manage_options(REQUEST=None):
        """
        """

    def manage_workspace(REQUEST):
        """Dispatch to first interface in manage_options
        """

    def tabs_path_default(REQUEST):
        """
        """

    def tabs_path_info(script, path):
        """
        """


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on OFS.SimpleItem.Item
class IItem(IZopeObject, IManageable, IFTPAccess, IDAVResource,
            ICopySource, ITraversable, IOwned, IUndoSupport):

    __name__ = BytesLine(
        title=u"Name"
        )

    title = BytesLine(
        title=u"Title"
        )

    icon = BytesLine(
        title=u"Icon",
        description=u"Name of icon, relative to BASEPATH1",
        )

    def getId():
        """Return the id of the object as a string.

        This method should be used in preference to accessing an id
        attribute of an object directly. The getId method is public.
        """

    def title_or_id():
        """Return the title if it is not blank and the id otherwise.
        """

    def title_and_id():
        """Return the title if it is not blank and the id otherwise.

        If the title is not blank, then the id is included in parens.
        """

    def manage_editedDialog(REQUEST, **args):
        """Show an 'edited' dialog.
        """

    def raise_standardErrorMessage(client=None, REQUEST={},
                                   error_type=None, error_value=None, tb=None,
                                   error_tb=None, error_message='',
                                   tagSearch=None, error_log_url=''):
        """Raise standard error message.
        """


# XXX: based on OFS.SimpleItem.Item_w__name__
class IItemWithName(IItem):

    """Item with name.
    """


# XXX: based on OFS.SimpleItem.SimpleItem
class ISimpleItem(IItem, IPersistent, IAcquirer, IRoleManager):

    """Not-so-simple item.
    """


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on OFS.CopySupport.CopyContainer
class ICopyContainer(Interface):

    """Interface for containerish objects which allow cut/copy/paste"""

    # The following three methods should be overridden to store sub-objects
    # as non-attributes.
    def _setOb(id, object):
        """
        """

    def _delOb(id):
        """
        """

    def _getOb(id, default=None):
        """
        """

    def manage_CopyContainerFirstItem(REQUEST):
        """
        """

    def manage_CopyContainerAllItems(REQUEST):
        """
        """

    def manage_cutObjects(ids=None, REQUEST=None):
        """Put a reference to the objects named in ids in the clip board"""

    def manage_copyObjects(ids=None, REQUEST=None, RESPONSE=None):
        """Put a reference to the objects named in ids in the clip board"""

    def _get_id(id):
        """Allow containers to override the generation of object copy id by
        attempting to call its _get_id method, if it exists.
        """

    def manage_pasteObjects(cb_copy_data=None, REQUEST=None):
        """Paste previously copied objects into the current object.

        If calling manage_pasteObjects from python code, pass the result of a
        previous call to manage_cutObjects or manage_copyObjects as the first
        argument.
        """

    manage_renameForm = Attribute("""Rename management view""")

    def manage_renameObjects(ids=[], new_ids=[], REQUEST=None):
        """Rename several sub-objects"""

    def manage_renameObject(id, new_id, REQUEST=None):
        """Rename a particular sub-object"""

    def manage_clone(ob, id, REQUEST=None):
        """Clone an object, creating a new object with the given id.
        """

    def cb_dataValid():
        """Return true if clipboard data seems valid.
        """

    def cb_dataItems():
        """List of objects in the clip board.
        """

    def _verifyObjectPaste(object, validate_src=1):
        """Verify whether the current user is allowed to paste the passed
        object into self. This is determined by checking to see if the
        user could create a new object of the same meta_type of the
        object passed in and checking that the user actually is
        allowed to access the passed in object in its existing
        context.

        Passing a false value for the validate_src argument will skip
        checking the passed in object in its existing context. This is
        mainly useful for situations where the passed in object has no
        existing context, such as checking an object during an import
        (the object will not yet have been connected to the
        acquisition hierarchy).
        """


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on OFS.ObjectManager.ObjectManager
class IObjectManager(IZopeObject, ICopyContainer, INavigation, IManageable,
                     IAcquirer, IPersistent, IDAVCollection, ITraversable,
                     IPossibleSite, IContainer):
    """Generic object manager

    This interface provides core behavior for collections of heterogeneous
    objects."""

    meta_types = Tuple(
        title=u"Meta types",
        description=u"Sub-object types that are specific to this object",
        )

    isAnObjectManager = Bool(
        title=u"Is an object manager",
        )

    manage_main = Attribute(""" """)
    manage_index_main = Attribute(""" """)
    manage_addProduct = Attribute(""" """)
    manage_importExportForm = Attribute(""" """)

    def all_meta_types(interfaces=None):
        """
        """

    def _subobject_permissions():
        """
        """

    def filtered_meta_types(user=None):
        """Return a list of the types for which the user has adequate
        permission to add that type of object.
        """

    def _setOb(id, object):
        """
        """

    def _delOb(id):
        """
        """

    def _getOb(id, default=None):
        """
        """

    def _setObject(id, object, roles=None, user=None, set_owner=1):
        """
        """

    def _delObject(id, dp=1):
        """
        """

    def hasObject(id):
        """Indicate whether the folder has an item by ID.
        """

    def objectIds(spec=None):
        """List the IDs of the subobjects of the current object.

        If 'spec' is specified, returns only objects whose meta_types match
        'spec'.
        """

    def objectValues(spec=None):
        """List the subobjects of the current object.

        If 'spec' is specified, returns only objects whose meta_types match
        'spec'.
        """

    def objectItems(spec=None):
        """List (ID, subobject) tuples for subobjects of the current object.

        If 'spec' is specified, returns only objects whose meta_types match
        'spec'.
        """

    def objectMap():
        """Return a tuple of mappings containing subobject meta-data.
        """

    def superValues(t):
        """Return all of the objects of a given type located in this object
        and containing objects.
        """

    def manage_delObjects(ids=[], REQUEST=None):
        """Delete a subordinate object

        The objects specified in 'ids' get deleted.
        """

    def tpValues():
        """Return a list of subobjects, used by tree tag.
        """

    def manage_exportObject(id='', download=None, toxml=None,
                            RESPONSE=None,REQUEST=None):
        """Exports an object to a file and returns that file."""

    def manage_importObject(file, REQUEST=None, set_owner=1):
        """Import an object from a file"""

    def _importObjectFromFile(filepath, verify=1, set_owner=1):
        """
        """


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on OFS.FindSupport.FindSupport
class IFindSupport(Interface):

    """Find support for Zope Folders"""

    manage_findFrame = Attribute(""" """)
    manage_findForm = Attribute(""" """)
    manage_findAdv = Attribute(""" """)
    manage_findResult = Attribute(""" """)

    def ZopeFind(obj, obj_ids=None, obj_metatypes=None,
                 obj_searchterm=None, obj_expr=None,
                 obj_mtime=None, obj_mspec=None,
                 obj_permission=None, obj_roles=None,
                 search_sub=0,
                 REQUEST=None, result=None, pre=''):
        """Zope Find interface"""

    PrincipiaFind = ZopeFind

    def ZopeFindAndApply(obj, obj_ids=None, obj_metatypes=None,
                         obj_searchterm=None, obj_expr=None,
                         obj_mtime=None, obj_mspec=None,
                         obj_permission=None, obj_roles=None,
                         search_sub=0,
                         REQUEST=None, result=None, pre='',
                         apply_func=None, apply_path=''):
        """Zope Find interface and apply"""


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on OFS.PropertyManager.PropertyManager
class IPropertyManager(Interface):

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

    manage_propertiesForm = Attribute(""" """)
    manage_propertyTypeForm = Attribute(""" """)

    title = BytesLine(
        title=u"Title"
        )

    _properties = Tuple(
        title=u"Properties",
        )

    propertysheets = Attribute(""" """)

    def valid_property_id(id):
        """
        """

    def hasProperty(id):
        """Return true if object has a property 'id'.
        """

    def getProperty(id, d=None):
        """Get the property 'id'.

        Returns the optional second argument or None if no such property is
        found.
        """

    def getPropertyType(id):
        """Get the type of property 'id'.

        Returns None if no such property exists.
        """

    def _wrapperCheck(object):
        """Raise an error if an object is wrapped.
        """

    def _setPropValue(id, value):
        """
        """

    def _delPropValue(id):
        """
        """

    def _setProperty(id, value, type='string'):
        """Set property.

        For selection and multiple selection properties the value argument
        indicates the select variable of the property.
        """

    def _updateProperty(id, value):
        """Update the value of an existing property.

        If value is a string, an attempt will be made to convert the value to
        the type of the existing property.
        """

    def _delProperty(id):
        """
        """

    def propertyIds():
        """Return a list of property ids.
        """

    def propertyValues():
        """Return a list of actual property objects.
        """

    def propertyItems():
        """Return a list of (id,property) tuples.
        """

    def _propertyMap():
        """Return a tuple of mappings, giving meta-data for properties.
        """

    def propertyMap():
        """Return a tuple of mappings, giving meta-data for properties.

        Return copies of the real definitions for security.
        """

    def propertyLabel(id):
        """Return a label for the given property id
        """

    def propdict():
        """
        """

    # Web interface

    def manage_addProperty(id, value, type, REQUEST=None):
        """Add a new property via the web.

        Sets a new property with the given id, type, and value.
        """

    def manage_editProperties(REQUEST):
        """Edit object properties via the web.

        The purpose of this method is to change all property values,
        even those not listed in REQUEST; otherwise checkboxes that
        get turned off will be ignored.  Use manage_changeProperties()
        instead for most situations.
        """

    def manage_changeProperties(REQUEST=None, **kw):
        """Change existing object properties.

        Change object properties by passing either a REQUEST object or
        name=value parameters
        """

    def manage_changePropertyTypes(old_ids, props, REQUEST=None):
        """Replace one set of properties with another

        Delete all properties that have ids in old_ids, then add a
        property for each item in props.  Each item has a new_id,
        new_value, and new_type.  The type of new_value should match
        new_type.
        """

    def manage_delProperties(ids=None, REQUEST=None):
        """Delete one or more properties specified by 'ids'."""


# XXX: based on OFS.Folder.Folder
class IFolder(IObjectManager, IPropertyManager, IRoleManager,
              IDAVCollection, IItem, IFindSupport):

    """Folders are basic container objects that provide a standard
    interface for object management. Folder objects also implement a
    management interface and can have arbitrary properties.
    """


# XXX: based on OFS.OrderedFolder.OrderedFolder
class IOrderedFolder(IOrderedContainer, IFolder):

    """Ordered folder.
    """


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on OFS.Application.Application
class IApplication(IFolder, IRoot):

    """Top-level system object"""

    isTopLevelPrincipiaApplicationObject = Bool(
        title=u"Is top level Principa application object",
        )

    HelpSys = Attribute("Help system")

    p_ = Attribute(""" """)
    misc_ = Attribute("Misc.")

    def PrincipiaRedirect(destination, URL1):
        """Utility function to allow user-controlled redirects"""

    Redirect = ZopeRedirect = PrincipiaRedirect

    def __bobo_traverse__(REQUEST, name=None):
        """Bobo traverse.
        """

    def PrincipiaTime(*args):
        """Utility function to return current date/time"""

    ZopeTime = PrincipiaTime

    def ZopeAttributionButton():
        """Returns an HTML fragment that displays the 'powered by zope'
        button along with a link to the Zope site."""

    test_url = ZopeAttributionButton

    def absolute_url(relative=0):
        """The absolute URL of the root object is BASE1 or "/".
        """

    def absolute_url_path():
        """The absolute URL path of the root object is BASEPATH1 or "/".
        """

    def virtual_url_path():
        """The virtual URL path of the root object is empty.
        """

    def getPhysicalRoot():
        """
        """


##################################################
# Event interfaces

from zope.component.interfaces import IObjectEvent

class IObjectWillBeMovedEvent(IObjectEvent):
    """An object will be moved."""
    oldParent = Attribute("The old location parent for the object.")
    oldName = Attribute("The old location name for the object.")
    newParent = Attribute("The new location parent for the object.")
    newName = Attribute("The new location name for the object.")

class IObjectWillBeAddedEvent(IObjectWillBeMovedEvent):
    """An object will be added to a container."""

class IObjectWillBeRemovedEvent(IObjectWillBeMovedEvent):
    """An object will be removed from a container"""

class IObjectClonedEvent(IObjectEvent):
    """An object has been cloned (a la Zope 2).

    This is for Zope 2 compatibility, subscribers should really use
    IObjectCopiedEvent or IObjectAddedEvent, depending on their use
    cases.

    event.object is the copied object, already added to its container.
    Note that this event is dispatched to all sublocations.
    """
