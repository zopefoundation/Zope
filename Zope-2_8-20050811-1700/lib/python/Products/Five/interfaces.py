##############################################################################
#
# Copyright (c) 2000-2005 Zope Corporation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Five interfaces

$Id: interfaces.py 12915 2005-05-31 10:23:19Z philikon $
"""
from zope.interface import Interface, Attribute
from zope.interface.interfaces import IInterface
from zope.schema import Bool, BytesLine, Tuple

try:
    from persistent.interfaces import IPersistent
except ImportError:
    class IPersistent(Interface):
        """Persistent object"""


class IPersistentExtra(Interface):

    def bobobase_modification_time():
        """ """

    def locked_in_version():
        """Was the object modified in any version?"""

    def modified_in_version():
        """Was the object modified in this version?"""


class IBrowserDefault(Interface):
    """Provide a hook for deciding about the default view for an object"""

    def defaultView(self, request):
        """Return the object to be published
        (usually self) and a sequence of names to traverse to
        find the method to be published.
        """


class IMenuItemType(IInterface):
    """Menu item type

    Menu item types are interfaces that define classes of
    menu items.
    """


#
# Zope 2.7 core interfaces
#

# based on Acquisition.*AcquisitionWrapper
class IAcquisitionWrapper(Interface):
    """ Wrapper object for acquisition.
    """

    def aq_acquire(name, filter=None, extra=None, explicit=True, default=0,
                   containment=0):
        """Get an attribute, acquiring it if necessary"""

    def aq_inContextOf(obj, inner=1):
        """Test whether the object is currently in the context of the
        argument"""


# based on Acquisition.*plicit
class IAcquisition(Interface):
    """ Acquire attributes from containers.
    """

    def __of__(context):
        """Return the object in a context"""


## XXX: these are wrapper attributes and/or module functions
##
##    def aq_acquire(name, filter=None, extra=None, explicit=None):
##        """Get an attribute, acquiring it if necessary"""
##
##    def aq_get(name, default=None):
##        """Get an attribute, acquiring it if necessary."""
##
##    # those are computed attributes, aren't they?
##
##    def aq_base():
##        """Get the object unwrapped"""
##
##    def aq_parent():
##        """Get the parent of an object"""
##
##    def aq_self():
##        """Get the object with the outermost wrapper removed"""
##
##    def aq_inner():
##        """Get the object with alll but the innermost wrapper removed"""
##
##    def aq_chain(containment=0):
##        """Get a list of objects in the acquisition environment"""


# based on OFS.SimpleItem.Item and Management.Tabs
class IManageable(Interface):
    """Something that is manageable in the ZMI"""

    def manage(URL1):
        """Show management screen"""

    def manage_afterAdd(item, container):
        """Gets called after being added to a container"""

    def manage_beforeDelete(item, container):
        """Gets called before being deleted"""

    def manage_afterClone(item):
        """Gets called after being cloned"""

    def manage_editedDialog(REQUEST, **args):
        """Show an 'edited' dialog"""

    def filtered_manage_options(REQUEST=None):
        """ """

    def manage_workspace(REQUEST):
        """Dispatch to first interface in manage_options"""

    def tabs_path_default(REQUEST):
        """ """

    def tabs_path_info(script, path):
        """ """

    def class_manage_path():
        """ """

    manage_options = Tuple(
        title=u"Manage options",
        )

    manage_tabs = Attribute("""Management tabs""")


# based on OFS.FTPInterface.FTPInterface
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


# copied from webdav.WriteLockInterface.WriteLockInterface
class IWriteLock(Interface):
    """This represents the basic protocol needed to support the write lock
    machinery.

    It must be able to answer the questions:

     o Is the object locked?

     o Is the lock owned by the current user?

     o What lock tokens are associated with the current object?

     o What is their state (how long until they're supposed to time out?,
       what is their depth?  what type are they?

    And it must be able to do the following:

     o Grant a write lock on the object to a specified user.

       - *If lock depth is infinite, this must also grant locks on **all**
         subobjects, or fail altogether*

     o Revoke a lock on the object.

       - *If lock depth is infinite, this must also revoke locks on all
         subobjects*

    **All methods in the WriteLock interface that deal with checking valid
    locks MUST check the timeout values on the lockitem (ie, by calling
    'lockitem.isValid()'), and DELETE the lock if it is no longer valid**
    """

    def wl_lockItems(killinvalids=0):
        """ Returns (key, value) pairs of locktoken, lock.

        if 'killinvalids' is true, invalid locks (locks whose timeout
        has been exceeded) will be deleted"""

    def wl_lockValues(killinvalids=0):
        """ Returns a sequence of locks.  if 'killinvalids' is true,
        invalid locks will be deleted"""

    def wl_lockTokens(killinvalids=0):
        """ Returns a sequence of lock tokens.  if 'killinvalids' is true,
        invalid locks will be deleted"""

    def wl_hasLock(token, killinvalids=0):
        """ Returns true if the lock identified by the token is attached
        to the object. """

    def wl_isLocked():
        """ Returns true if 'self' is locked at all.  If invalid locks
        still exist, they should be deleted."""

    def wl_setLock(locktoken, lock):
        """ Store the LockItem, 'lock'.  The locktoken will be used to fetch
        and delete the lock.  If the lock exists, this MUST
        overwrite it if all of the values except for the 'timeout' on the
        old and new lock are the same. """

    def wl_getLock(locktoken):
        """ Returns the locktoken identified by the locktokenuri """

    def wl_delLock(locktoken):
        """ Deletes the locktoken identified by the locktokenuri """

    def wl_clearLocks():
        """ Deletes ALL DAV locks on the object - should only be called
        by lock management machinery. """


# based on webdav.Resource.Resource
class IDAVResource(IWriteLock):
    """Provide basic WebDAV support for non-collection objects."""

    __dav_resource__ = Bool(
        title=u"Is DAV resource"
        )

    __http_methods__ = Tuple(
        title=u"HTTP methods",
        description=u"Sequence of valid HTTP methods"
        )

    def dav__init(request, response):
        """
        Init expected HTTP 1.1 / WebDAV headers which are not
        currently set by the base response object automagically.

        Note we set an borg-specific header for ie5 :( Also, we sniff
        for a ZServer response object, because we don't want to write
        duplicate headers (since ZS writes Date and Connection
        itself)."""

    def dav__validate(object, methodname, REQUEST):
        """ """

    def dav__simpleifhandler(request, response, method='PUT',
                             col=0, url=None, refresh=0):
        """ """

    def HEAD(REQUEST, RESPONSE):
        """Retrieve resource information without a response body."""

    def PUT(REQUEST, RESPONSE):
        """Replace the GET response entity of an existing resource.
        Because this is often object-dependent, objects which handle
        PUT should override the default PUT implementation with an
        object-specific implementation. By default, PUT requests
        fail with a 405 (Method Not Allowed)."""

    def OPTIONS(REQUEST, RESPONSE):
        """Retrieve communication options."""

    def TRACE(REQUEST, RESPONSE):
        """Return the HTTP message received back to the client as the
        entity-body of a 200 (OK) response. This will often usually
        be intercepted by the web server in use. If not, the TRACE
        request will fail with a 405 (Method Not Allowed), since it
        is not often possible to reproduce the HTTP request verbatim
        from within the Zope environment."""

    def DELETE(REQUEST, RESPONSE):
        """Delete a resource. For non-collection resources, DELETE may
        return either 200 or 204 (No Content) to indicate success."""

    def PROPFIND(REQUEST, RESPONSE):
        """Retrieve properties defined on the resource."""

    def PROPPATCH(REQUEST, RESPONSE):
        """Set and/or remove properties defined on the resource."""

    def MKCOL(REQUEST, RESPONSE):
        """Create a new collection resource. If called on an existing
        resource, MKCOL must fail with 405 (Method Not Allowed)."""

    def COPY(REQUEST, RESPONSE):
        """Create a duplicate of the source resource whose state
        and behavior match that of the source resource as closely
        as possible. Though we may later try to make a copy appear
        seamless across namespaces (e.g. from Zope to Apache), COPY
        is currently only supported within the Zope namespace."""

    def MOVE(REQUEST, RESPONSE):
        """Move a resource to a new location. Though we may later try to
        make a move appear seamless across namespaces (e.g. from Zope
        to Apache), MOVE is currently only supported within the Zope
        namespace."""

    def LOCK(REQUEST, RESPONSE):
        """Lock a resource"""

    def UNLOCK(REQUEST, RESPONSE):
        """Remove an existing lock on a resource."""

    def manage_DAVget():
        """Gets the document source"""

    def listDAVObjects():
        """ """


# based on OFS.CopySupport.CopySource
class ICopySource(Interface):
    """Interface for objects which allow themselves to be copied."""

    def _canCopy(op=0):
        """Called to make sure this object is copyable. The op var
        is 0 for a copy, 1 for a move."""

    def _notifyOfCopyTo(container, op=0):
        """Overide this to be pickly about where you go! If you dont
        want to go there, raise an exception. The op variable is
        0 for a copy, 1 for a move."""

    def _getCopy(container):
        """
        Commit a subtransaction to:
        1) Make sure the data about to be exported is current
        2) Ensure self._p_jar and container._p_jar are set even if
           either one is a new object
        """

    def _postCopy(container, op=0):
        """Called after the copy is finished to accomodate special cases.
        The op var is 0 for a copy, 1 for a move."""

    def _setId(id):
        """Called to set the new id of a copied object."""

    def cb_isCopyable():
        """Is object copyable? Returns 0 or 1"""

    def cb_isMoveable():
        """Is object moveable? Returns 0 or 1"""

    def cb_userHasCopyOrMovePermission():
        """ """


# based on OFS.Traversable.Traversable
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
        '''Returns a path (an immutable sequence of strings)
        that can be used to access this object again
        later, for example in a copy/paste operation.  getPhysicalRoot()
        and getPhysicalPath() are designed to operate together.
        '''

    def unrestrictedTraverse(path, default=None, restricted=0):
        """Lookup an object by path,

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
        """Trusted code traversal code, always enforces security"""


# based on AccessControl.Owned.Owned
class IOwned(Interface):

    manage_owner = Attribute("""Manage owner view""")

    def owner_info():
        """Get ownership info for display"""

    def getOwner(info=0):
        """Get the owner

        If a true argument is provided, then only the owner path and id are
        returned. Otherwise, the owner object is returned.
        """

    def getOwnerTuple():
        """Return a tuple, (userdb_path, user_id) for the owner.

        o Ownership can be acquired, but only from the containment path.

        o If unowned, return None.
        """

    def getWrappedOwner():
        """Get the owner, modestly wrapped in the user folder.

        o If the object is not owned, return None.

        o If the owner's user database doesn't exist, return Nobody.

        o If the owner ID does not exist in the user database, return Nobody.
        """

    def changeOwnership(user, recursive=0):
        """Change the ownership to the given user.  If 'recursive' is
        true then also take ownership of all sub-objects, otherwise
        sub-objects retain their ownership information."""

    def userCanTakeOwnership():
        """ """

    def manage_takeOwnership(REQUEST, RESPONSE, recursive=0):
        """Take ownership (responsibility) for an object. If 'recursive'
        is true, then also take ownership of all sub-objects.
        """

    def manage_changeOwnershipType(explicit=1, RESPONSE=None, REQUEST=None):
        """Change the type (implicit or explicit) of ownership.
        """

    def _deleteOwnershipAfterAdd():
        """ """

    def manage_fixupOwnershipAfterAdd():
        """ """


# based on App.Undo.UndoSupport
class IUndoSupport(Interface):

    manage_UndoForm = Attribute("""Manage Undo form""")

    def get_request_var_or_attr(name, default):
        """ """

    def undoable_transactions(first_transaction=None,
                              last_transaction=None,
                              PrincipiaUndoBatchSize=None):
        """ """

    def manage_undo_transactions(transaction_info=(), REQUEST=None):
        """ """


# based on many classes
class IZopeObject(Interface):

    isPrincipiaFolderish = Bool(
        title=u"Is a folderish object",
        description=u"Should be false for simple items",
        )

    meta_type = BytesLine(
        title=u"Meta type",
        description=u"The object's Zope2 meta type",
        )


# based on OFS.SimpleItem.Item
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
        description=u"Name of icon, relative to SOFTWARE_URL",
        )

    def getId():
        """Return the id of the object as a string.

        This method should be used in preference to accessing an id
        attribute of an object directly. The getId method is public.
        """

    def title_or_id():
        """Returns the title if it is not blank and the id otherwise."""

    def title_and_id():
        """Returns the title if it is not blank and the id otherwise.  If the
        title is not blank, then the id is included in parens."""

    def raise_standardErrorMessage(client=None, REQUEST={},
                                   error_type=None, error_value=None, tb=None,
                                   error_tb=None, error_message='',
                                   tagSearch=None, error_log_url=''):
        """Raise standard error message"""


# based on OFS.SimpleItem.Item_w__name__
class IItemWithName(IItem):
    """Item with name"""

    def _setId(id):
        """Set the id"""

    def getPhysicalPath():
        """Returns a path (an immutable sequence of strings) that can be used
        to access this object again later, for example in a copy/paste
        operation."""


# based on AccessControl.PermissionMapping.RoleManager
class IPermissionMapping(Interface):

    def manage_getPermissionMapping():
        """Return the permission mapping for the object

        This is a list of dictionaries with:

          permission_name -- The name of the native object permission

          class_permission -- The class permission the permission is
             mapped to.
        """

    def manage_setPermissionMapping(permission_names=[],
                                    class_permissions=[], REQUEST=None):
        """Change the permission mapping"""


# based on AccessControl.Role.RoleManager
class IRoleManager(IPermissionMapping):
    """An object that has configurable permissions"""

    permissionMappingPossibleValues = Attribute("""Acquired attribute""")

    def ac_inherited_permissions(all=0):
        """Get all permissions not defined in ourself that are inherited This
        will be a sequence of tuples with a name as the first item and
        an empty tuple as the second."""

    def permission_settings(permission=None):
        """Return user-role permission settings. If 'permission' is passed to
        the method then only the settings for 'permission' returned."""

    manage_roleForm = Attribute(""" """)

    def manage_role(role_to_manage, permissions=[], REQUEST=None):
        """Change the permissions given to the given role"""

    manage_acquiredForm = Attribute(""" """)

    def manage_acquiredPermissions(permissions=[], REQUEST=None):
        """Change the permissions that acquire"""

    manage_permissionForm = Attribute(""" """)

    def manage_permission(permission_to_manage, roles=[], acquire=0,
                          REQUEST=None):
        """Change the settings for the given permission

        If optional arg acquire is true, then the roles for the permission
        are acquired, in addition to the ones specified, otherwise the
        permissions are restricted to only the designated roles."""

    def manage_access(REQUEST, **kw):
        """Return an interface for making permissions settings"""

    def manage_changePermissions(REQUEST):
        """Change all permissions settings, called by management screen"""

    def permissionsOfRole(role):
        """used by management screen"""

    def rolesOfPermission(permission):
        """used by management screen"""

    def acquiredRolesAreUsedBy(permission):
        """used by management screen"""


    # Local roles support
    # -------------------
    #
    # Local roles allow a user to be given extra roles in the context
    # of a particular object (and its children). When a user is given
    # extra roles in a particular object, an entry for that user is made
    # in the __ac_local_roles__ dict containing the extra roles.

    __ac_local_roles__  = Attribute(""" """)

    manage_listLocalRoles = Attribute(""" """)

    manage_editLocalRoles = Attribute(""" """)

    def has_local_roles():
        """ """

    def get_local_roles():
        """ """

    def users_with_local_role(role):
        """ """

    def get_valid_userids():
        """ """

    def get_local_roles_for_userid(userid):
        """ """

    def manage_addLocalRoles(userid, roles, REQUEST=None):
        """Set local roles for a user."""

    def manage_setLocalRoles(userid, roles, REQUEST=None):
        """Set local roles for a user."""

    def manage_delLocalRoles(userids, REQUEST=None):
        """Remove all local roles for a user."""

    #------------------------------------------------------------

    def access_debug_info():
        """Return debug info"""

    def valid_roles():
        """Return list of valid roles"""

    def validate_roles(roles):
        """Return true if all given roles are valid"""

    def userdefined_roles():
        """Return list of user-defined roles"""

    def manage_defined_roles(submit=None, REQUEST=None):
        """Called by management screen."""

    def _addRole(role, REQUEST=None):
        """ """

    def _delRoles(roles, REQUEST=None):
        """ """

    def _has_user_defined_role(role):
        """ """

    def manage_editRoles(REQUEST, acl_type='A', acl_roles=[]):
        """ """

    def _setRoles(acl_type, acl_roles):
        """ """

    def possible_permissions():
        """ """


# based on OFS.SimpleItem.SimpleItem
class ISimpleItem(IItem, IPersistent, IAcquisition, IRoleManager):
    """Not-so-simple item"""


# based on OFS.CopySupport.CopyContainer
class ICopyContainer(Interface):
    """Interface for containerish objects which allow cut/copy/paste"""

    # The following three methods should be overridden to store sub-objects
    # as non-attributes.
    def _setOb(id, object):
        """ """

    def _delOb(id):
        """ """

    def _getOb(id, default=None):
        """ """

    def manage_CopyContainerFirstItem(REQUEST):
        """ """

    def manage_CopyContainerAllItems(REQUEST):
        """ """

    def manage_cutObjects(ids=None, REQUEST=None):
        """Put a reference to the objects named in ids in the clip board"""

    def manage_copyObjects(ids=None, REQUEST=None, RESPONSE=None):
        """Put a reference to the objects named in ids in the clip board"""

    def _get_id(id):
        """Allow containers to override the generation of object copy id by
        attempting to call its _get_id method, if it exists."""

    def manage_pasteObjects(cb_copy_data=None, REQUEST=None):
        """Paste previously copied objects into the current object.  If
        calling manage_pasteObjects from python code, pass the result
        of a previous call to manage_cutObjects or manage_copyObjects
        as the first argument."""

    manage_renameForm = Attribute("""Rename management view""")

    def manage_renameObjects(ids=[], new_ids=[], REQUEST=None):
        """Rename several sub-objects"""

    def manage_renameObject(id, new_id, REQUEST=None):
        """Rename a particular sub-object"""

    def manage_clone(ob, id, REQUEST=None):
        """Clone an object, creating a new object with the given id."""

    def cb_dataValid():
        """Return true if clipboard data seems valid."""

    def cb_dataItems():
        """List of objects in the clip board"""

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
        acquisition hierarchy)."""


# based on App.Management.Navigation
class INavigation(Interface):
    """Basic navigation UI support"""

    manage = Attribute(""" """)
    manage_menu = Attribute(""" """)
    manage_top_frame = Attribute(""" """)
    manage_page_header = Attribute(""" """)
    manage_page_footer = Attribute(""" """)
    manage_form_title = Attribute("""Add Form""")
    zope_quick_start = Attribute(""" """)
    manage_copyright = Attribute(""" """)
    manage_zmi_prefs = Attribute(""" """)

    def manage_zmi_logout(REQUEST, RESPONSE):
        """Logout current user"""

INavigation.setTaggedValue('manage_page_style.css', Attribute(""" """))


# based on webdav.Collection.Collection
class IDAVCollection(IDAVResource):
    """The Collection class provides basic WebDAV support for collection
    objects. It provides default implementations for all supported
    WebDAV HTTP methods. The behaviors of some WebDAV HTTP methods for
    collections are slightly different than those for non-collection
    resources."""

    __dav_collection__ = Bool(
        title=u"Is a DAV collection",
        description=u"Should be true",
        )

    def dav__init(request, response):
        """ """

    def HEAD(REQUEST, RESPONSE):
        """Retrieve resource information without a response body."""

    def PUT(REQUEST, RESPONSE):
        """The PUT method has no inherent meaning for collection
        resources, though collections are not specifically forbidden
        to handle PUT requests. The default response to a PUT request
        for collections is 405 (Method Not Allowed)."""

    def DELETE(REQUEST, RESPONSE):
        """Delete a collection resource. For collection resources, DELETE
        may return either 200 (OK) or 204 (No Content) to indicate total
        success, or may return 207 (Multistatus) to indicate partial
        success. Note that in Zope a DELETE currently never returns 207."""

    def listDAVObjects():
        """ """


# based on OFS.ObjectManager.ObjectManager
class IObjectManager(IZopeObject, ICopyContainer, INavigation, IManageable,
                     IAcquisition, IPersistent, IDAVCollection, ITraversable):
    """Generic object manager

    This interface provides core behavior for collections of
    heterogeneous objects."""


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
        """ """

    def filtered_meta_types(user=None):
        """Return a list of the types for which the user has adequate
        permission to add that type of object."""

    def _setOb(id, object):
        """ """

    def _delOb(id):
        """ """

    def _getOb(id, default=None):
        """ """

    def _setObject(id, object, roles=None, user=None, set_owner=1):
        """ """

    def _delObject(id, dp=1):
        """ """

    def objectIds(spec=None):
        """Returns a list of subobject ids of the current object.  If 'spec'
        is specified, returns objects whose meta_type matches 'spec'.
        """

    def objectValues(spec=None):
        """Returns a list of actual subobjects of the current object.  If
        'spec' is specified, returns only objects whose meta_type
        match 'spec'."""

    def objectItems(spec=None):
        """Returns a list of (id, subobject) tuples of the current object.  If
        'spec' is specified, returns only objects whose meta_type
        match 'spec'"""

    def objectMap():
        """Return a tuple of mappings containing subobject meta-data"""

    def superValues(t):
        """Return all of the objects of a given type located in this object
        and containing objects."""

    def manage_delObjects(ids=[], REQUEST=None):
        """Delete a subordinate object

        The objects specified in 'ids' get deleted.
        """

    def tpValues():
        """Return a list of subobjects, used by tree tag."""

    def manage_exportObject(id='', download=None, toxml=None,
                            RESPONSE=None,REQUEST=None):
        """Exports an object to a file and returns that file."""

    def manage_importObject(file, REQUEST=None, set_owner=1):
        """Import an object from a file"""

    def _importObjectFromFile(filepath, verify=1, set_owner=1):
        """ """

    def __getitem__(key):
        """ """


# based on OFS.PropertyManager.PropertyManager
class IPropertyManager(Interface):
    """The PropertyManager mixin class provides an object with
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
        """ """

    def hasProperty(id):
        """Return true if object has a property 'id'"""

    def getProperty(id, d=None):
        """Get the property 'id', returning the optional second
           argument or None if no such property is found."""

    def getPropertyType(id):
        """Get the type of property 'id', returning None if no
           such property exists"""

    def _setProperty(id, value, type='string'):
        """ """

    def _updateProperty(id, value):
        """Update the value of an existing property. If value is a string, an
        attempt will be made to convert the value to the type of the
        existing property."""

    def _delProperty(id):
        """ """

    def propertyIds():
        """Return a list of property ids """

    def propertyValues():
        """Return a list of actual property objects """

    def propertyItems():
        """Return a list of (id,property) tuples """

    def _propertyMap():
        """Return a tuple of mappings, giving meta-data for properties """

    def propertyMap():
        """Return a tuple of mappings, giving meta-data for properties.
        Return copies of the real definitions for security.
        """

    def propertyLabel(id):
        """Return a label for the given property id
        """

    def propdict():
        """ """

    # Web interface

    def manage_addProperty(id, value, type, REQUEST=None):
        """Add a new property via the web. Sets a new property with
        the given id, type, and value."""

    def manage_editProperties(REQUEST):
        """Edit object properties via the web.
        The purpose of this method is to change all property values,
        even those not listed in REQUEST; otherwise checkboxes that
        get turned off will be ignored.  Use manage_changeProperties()
        instead for most situations.
        """

    def manage_changeProperties(REQUEST=None, **kw):
        """Change existing object properties.

        Change object properties by passing either a mapping object
        of name:value pairs {'foo':6} or passing name=value parameters
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


# based on OFS.FindSupport.FindSupport
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


# based on OFS.Folder.Folder
class IFolder(IObjectManager, IPropertyManager, IRoleManager,
              IDAVCollection, IItem, IFindSupport):
    """Folders are basic container objects that provide a standard
    interface for object management. Folder objects also implement a
    management interface and can have arbitrary properties."""


# copied from OFS.IOrderSupport.IOrderedContainer
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


# based on OFS.OrderedFolder.OrderedFolder
class IOrderedFolder(IOrderedContainer, IFolder):
    """Ordered folder"""


# based on OFS.Application.Application
class IApplication(IFolder, IFindSupport):
    """Top-level system object"""

    isTopLevelPrincipiaApplicationObject = Bool(
        title=u"Is top level Principa application object",
        )

    HelpSys = Attribute("Help system")

    p_ = Attribute(""" """)
    misc_ = Attribute("Misc.")

    def PrincipiaRedirect(destination,URL1):
        """Utility function to allow user-controlled redirects"""

    Redirect = ZopeRedirect = PrincipiaRedirect

    def __bobo_traverse__(REQUEST, name=None):
        """Bobo traverse"""

    def PrincipiaTime(*args):
        """Utility function to return current date/time"""

    ZopeTime = PrincipiaTime

    def ZopeAttributionButton():
        """Returns an HTML fragment that displays the 'powered by zope'
        button along with a link to the Zope site."""

    test_url = ZopeAttributionButton

    def absolute_url(relative=0):
        '''The absolute URL of the root object is BASE1 or "/".'''

    def absolute_url_path():
        '''The absolute URL path of the root object is BASEPATH1 or "/".'''

    def virtual_url_path():
        '''The virtual URL path of the root object is empty.'''

    def getPhysicalPath():
        '''Returns a path that can be used to access this object again
        later, for example in a copy/paste operation.  Designed to
        be used with getPhysicalRoot().
        '''

    def getPhysicalRoot():
        """Returns self"""

    def fixupZClassDependencies(rebuild=0):
        """ """

    def checkGlobalRegistry():
        """Check the global (zclass) registry for problems, which can
        be caused by things like disk-based products being deleted.
        Return true if a problem is found"""
