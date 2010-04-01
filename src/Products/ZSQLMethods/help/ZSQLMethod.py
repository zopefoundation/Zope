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

def manage_addZSQLMethod(id, title,
                         connection_id, arguments, template):
    """

    Add an SQL Method to an ObjectManager.

    The 'connection_id' argument is the id of a database connection
    that resides in the current folder or in a folder above the
    current folder.  The database should understand SQL.

    The 'arguments' argument is a string containing an arguments
    specification, as would be given in the SQL method cration form.

    The 'template' argument is a string containing the source for the
    SQL Template.

    """


class ZSQLMethod:
    """

    ZSQLMethods abstract SQL code in Zope.

    SQL Methods behave like methods of the folders they are
    accessed in.  In particular, they can be used from other
    methods, like Documents, ExternalMethods, and even other SQL
    Methods.

    Database methods support the Searchable Object Interface.
    Search interface wizards can be used to build user
    interfaces to them.  They can be used in joins and
    unions. They provide meta-data about their input parameters
    and result data.

    For more information, see the searchable-object interface
    specification.

    Database methods support URL traversal to access and invoke
    methods on individual record objects. For example, suppose you
    had an 'employees' database method that took a single argument
    'employee_id'.  Suppose that employees had a 'service_record'
    method (defined in a record class or acquired from a
    folder). The 'service_record' method could be accessed with a
    URL like::

       employees/employee_id/1234/service_record

    Search results are returned as Record objects.  The schema of
    a Record objects matches the schema of the table queried in
    the search.

    """

    __constructor__=manage_addZSQLMethod

    def __call__(REQUEST=None, **kw):
        """

        Call the ZSQLMethod.

        The arguments to the method should be passed via keyword
        arguments, or in a single mapping object. If no arguments are
        given, and if the method was invoked through the Web, then the
        method will try to acquire and use the Web REQUEST object as
        the argument mapping.

        The returned value is a sequence of record objects.

        """


    def manage_edit(title,connection_id,arguments,template):
        """

        Change database method properties.

        The 'connection_id' argument is the id of a database
        connection that resides in the current folder or in a folder
        above the current folder.  The database should understand SQL.

        The 'arguments' argument is a string containing an arguments
        specification, as would be given in the SQL method creation
        form.

        The 'template' argument is a string containing the source for
        the SQL Template.

        """
