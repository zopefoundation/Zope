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

class ObjectManagerItem:
    """
    A Zope object that can be contained within an Object Manager.
    Almost all Zope objects that can be managed through the web are
    Object Manager Items.

    ObjectMangerItems have these instance
    attributes:

      'title' -- The title of the object.

        This is an optional one-line string description of the object.

      'meta_type' --  A short name for the type of the object.

        This is the name that shows up in product add list for the
        object and is used when filtering objects by type.

        This attribute is provided by the object's class and should
        not be changed directly.

      'REQUEST' -- The current web request.

        This object is acquired and should not be set.
    """

    def getId():
        """
        Returns the object's id.

        The 'id' is the unique name of the object within its parent
        object manager. This should be a string, and can contain
        letters, digits, underscores, dashes, commas, and spaces.

        This method replaces direct access to the 'id' attribute.

        Permission -- Always available
        """

    def title_or_id():
        """
        If the title is not blank, return it, otherwise
        return the id.

        Permission -- Always available
        """

    def title_and_id():
        """
        If the title is not blank, the return the title
        followed by the id in parentheses. Otherwise return the id.

        Permission -- Always available
        """

    def manage_workspace():
        """

        This is the web method that is called when a user selects an
        item in a object manager contents view or in the Zope
        Management navigation view.

        Permission -- 'View management screens'
        """

    def this():
        """
        Return the object.

        This turns out to be handy in two situations. First, it
        provides a way to refer to an object in DTML expressions.

        The second use for this is rather deep. It provides a way to
        acquire an object without getting the full context that it was
        acquired from.  This is useful, for example, in cases where
        you are in a method of a non-item subobject of an item and you
        need to get the item outside of the context of the subobject.

        Permission -- Always available
        """

    def absolute_url(relative=None):
        """
        Return the absolute URL of the object.

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

        Permission -- Always available
        """

    def absolute_url_path():
        """
        Return the path portion of the absolute URL of the object.

        This includes the leading slash, and can be used as an
        'absolute-path reference' as defined in RFC 2396.

        Permission -- Always available
        """

    def virtual_url_path():
        """
        Return a URL for the object, relative to the site root.

        If a virtual host is configured, the URL is a path relative to
        the virtual host's root object.  Otherwise, it is the physical
        path.  In either case, the URL does not begin with a slash.

        

        Permission -- Always available
        """

    def getPhysicalRoot():
        """
        Returns the top-level Zope Application object.

        Permission -- Python only
        """

    def getPhysicalPath():
        """
        Get the path of an object from the root, ignoring virtual
        hosts.

        Permission -- Always available

        """

    def unrestrictedTraverse(path, default=None):
        """
        Return the object obtained by traversing the given path from
        the object on which the method was called. This method begins
        with "unrestricted" because (almost) no security checks are
        performed.

        If an object is not found then the 'default' argument will be
        returned.

        Permission -- Python only
        """

    def restrictedTraverse(path, default=None):
        """
        Return the object obtained by traversing the given path from
        the object on which the method was called, performing security
        checks along the way.

        If an object is not found then the 'default' argument will be
        returned.

        Permission -- Always available
        """
