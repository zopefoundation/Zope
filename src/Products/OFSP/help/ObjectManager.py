##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

class ObjectManager:
    """
    An ObjectManager contains other Zope objects. The contained
    objects are Object Manager Items.

    To create an object inside an object manager use 'manage_addProduct'::

      self.manage_addProduct['OFSP'].manage_addFolder(id, title)

    In DTML this would be::

        <dtml-call "manage_addProduct['OFSP'].manage_addFolder(id, title)">

    These examples create a new Folder inside the current
    ObjectManager.

    'manage_addProduct' is a mapping that provides access to product
    constructor methods. It is indexed by product id.

    Constructor methods are registered during product initialization
    and should be documented in the API docs for each addable
    object.
    """

    def objectIds(type=None):
        """
        This method returns a list of the ids of the contained
        objects.

        Optionally, you can pass an argument specifying what object
        meta_type(es) to restrict the results to. This argument can be
        a string specifying one meta_type, or it can be a list of
        strings to specify many.

        Example::

          <dtml-in objectIds>
            <dtml-var sequence-item>
          <dtml-else>
            There are no sub-objects.
          </dtml-in>

        This DTML code will display all the ids of the objects
        contained in the current Object Manager.

        Permission -- 'Access contents information'
        """

    def objectValues(type=None):
        """
        This method returns a sequence of contained objects.

        Like objectItems and objectIds, it accepts one argument,
        either a string or a list to restrict the results to objects
        of a given meta_type or set of meta_types.

        Example::

          <dtml-in expr="objectValues('Folder')">
            <dtml-var icon>
            This is the icon for the: <dtml-var id> Folder<br>.
          <dtml-else>
            There are no Folders.
          </dtml-in>

        The results were restricted to Folders by passing a
        meta_type to 'objectValues' method.

        Permission -- 'Access contents information'
        """

    def objectItems(type=None):
        """
        This method returns a sequence of (id, object) tuples.

        Like objectValues and objectIds, it accepts one argument,
        either a string or a list to restrict the results to objects
        of a given meta_type or set of meta_types.

        Each tuple's first element is the id of an object contained in
        the Object Manager, and the second element is the object
        itself.

        Example::

          <dtml-in objectItems>
           id: <dtml-var sequence-key>,
           type: <dtml-var meta_type>
          <dtml-else>
            There are no sub-objects.
          </dtml-in>

        Permission -- 'Access contents information'
        """

    def superValues(type):
        """
        This method returns a list of objects of a given meta_type(es)
        contained in the Object Manager and all its parent Object
        Managers.

        The type argument specifies the meta_type(es). It can be a string
        specifying one meta_type, or it can be a list of strings to
        specify many.

        Permission -- Python only
        """

    def manage_delObjects(ids):
        """
        Removes one or more children from the Object Manager. The
        'ids' argument is either a list of child ids, or a single
        child id.

        Permission -- 'Delete objects'
        """

    def __getitem__(id):
        """
        Returns a child object given a child id. If there is no child
        with the given id, a KeyError is raised. This method makes it easy
        to refer to children that have id with file extensions. For
        example::

          page=folder['index.html']

        Note: this function only finds children; it doesn't return
        properties or other non-child attributes.

        Note: this function doesn't use acquisition to find
        children. It only returns direct children of the Object
        Manager. By contrast, using dot notation or 'getattr' will
        locate children (and other attributes) via acquisition if
        necessary.

        Permission -- 'Access contents information'
        """

    def setBrowserDefaultId(id='', acquire=0):
        """
        Sets the id of the object or method used as the default method when
        the object manager is published. If acquire is set then the default
        method id will be acquired from the parent container.

        Permission -- 'Manage folderish settings'
        """

    def getBrowserDefaultId(acquire=0):
        """
        Returns the id of the object or method used as the default when the
        object manager is published. By default, this setting is acquired. If
        the acquire argument is true, then the return value will be acquired
        from the parent if it is not set locally. Otherwise, None is returned
        if the default id is not set on this object manager.

        Permission -- 'View'
        """
