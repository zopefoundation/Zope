##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

Revision information:
$Id$
"""

from IElement import IElement

class IInterface(IElement):
    """Interface objects

    Interface objects describe the behavior of an object by containing
    useful information about the object.  This information includes:

      o Prose documentation about the object.  In Python terms, this
        is called the "doc string" of the interface.  In this element,
        you describe how the object works in prose language and any
        other useful information about the object.

      o Descriptions of attributes.  Attribute descriptions include
        the name of the attribute and prose documentation describing
        the attributes usage.

      o Descriptions of methods.  Method descriptions can include:

        o Prose "doc string" documentation about the method and its
          usage.

        o A description of the methods arguments; how many arguments
          are expected, optional arguments and their default values,
          the position or arguments in the signature, whether the
          method accepts arbitrary arguments and whether the method
          accepts arbitrary keyword arguments.

      o Optional tagged data.  Interface objects (and their attributes and
        methods) can have optional, application specific tagged data
        associated with them.  Examples uses for this are examples,
        security assertions, pre/post conditions, and other possible
        information you may want to associate with an Interface or its
        attributes.

    Not all of this information is mandatory.  For example, you may
    only want the methods of your interface to have prose
    documentation and not describe the arguments of the method in
    exact detail.  Interface objects are flexible and let you give or
    take any of these components.

    Interfaces are created with the Python class statement using
    either Interface.Interface or another interface, as in::

      from Interface import Interface

      class IMyInterface(Interface):
        '''Interface documentation
        '''

        def meth(arg1, arg2):
            '''Documentation for meth
            '''

        # Note that there is no self argument

     class IMySubInterface(IMyInterface):
        '''Interface documentation
        '''

        def meth2():
            '''Documentation for meth2
            '''

    You use interfaces in two ways:

    o You assert that your object implement the interfaces.

      There are several ways that you can assert that an object
      implements an interface::

      1. Include an '__implements__' attribute in the object's class
         definition. The value of the '__implements__' attribute must
         be an implementation specification. An implementation
         specification is either an interface or a tuple of
         implementation specifications.

      2. Incluse an '__implements__' attribute in the object.
         Because Python classes don't have their own attributes, to
         assert that a class implements interfaces, you must provide a
         '__class_implements__' attribute in the class definition.

         **Important**: A class usually doesn't implement the
           interfaces that it's instances implement. The class and
           it's instances are separate objects with their own
           interfaces.

      3. Call 'Interface.Implements.implements' to assert that instances
         of a class implement an interface.

         For example::

           from Interface.Implements import implements

           implements(some_class, some_interface)

         This is approach is useful when it is not an option to modify
         the class source.  Note that this doesn't affect what the
         class itself implements, but only what it's instances
         implement.

      4. For types that can't be modified, you can assert that
         instances of the type implement an interface using
         'Interface.Implements.assertTypeImplements'.

         For example::

           from Interface.Implements import assertTypeImplements

           assertTypeImplements(some_type, some_interface)

    o You query interface meta-data. See the IInterface methods and
      attributes for details.

    """

    def getBases():
        """Return a sequence of the base interfaces
        """

    def extends(other, strict=1):
        """Test whether the interface extends another interface

        A true value is returned in the interface extends the other
        interface, and false otherwise.

        Normally, an interface doesn't extend itself. If a false value
        is passed as the second argument, or via the 'strict' keyword
        argument, then a true value will be returned if the interface
        and the other interface are the same.
        """

    def isImplementedBy(object):
        """Test whether the interface is implemented by the object.

        Return true of the object asserts that it implements the
        interface, including asseting that it implements an extended
        interface.
        """

    def isImplementedByInstancesOf(class_):
        """Test whether the interface is implemented by instances of the class

        Return true of the class asserts that it's instances implement the
        interface, including asseting that they implement an extended
        interface.
        """
    def names(all=0):
        """Get the interface attribute names.

        Return a sequence of the names of the attributes, including
        methods, included in the interface definition.

        Normally, only directly defined attributes are included. If
        a true positional or keyword argument is given, then
        attributes defined by nase classes will be included.
        """

    def namesAndDescriptions(all=0):
        """Get the interface attribute names and descriptions.

        Return a sequence of the names and descriptions of the
        attributes, including methods, as name-value pairs, included
        in the interface definition.

        Normally, only directly defined attributes are included. If
        a true positional or keyword argument is given, then
        attributes defined by nase classes will be included.
        """

    def getDescriptionFor(name):
        """Get the description for a name

        If the named attribute does not exist, a KeyError is raised.
        """

    def queryDescriptionFor(name, default=None):
        """Get the description for a name

        Return the default if no description exists.
        """
