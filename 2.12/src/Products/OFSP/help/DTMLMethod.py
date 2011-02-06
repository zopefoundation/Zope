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

def manage_addDTMLMethod(id, title):
    """
    Add a DTML Method to the current ObjectManager
    """

class DTMLMethod:
    """
    A DTML Method is a Zope object that contains and executes DTML
    code. It can act as a template to display other objects. It can
    also hold small pieces of content which are inserted into other
    DTML Documents or DTML Methods.

    The DTML Method's id is available via the 'document_id'
    variable and the title is available via the 'document_title'
    variable.

    """

    __extends__=('OFSP.ObjectManagerItem.ObjectManagerItem',)

    def __call__(client=None, REQUEST={}, **kw):
        """

        Calling a DTMLMethod causes the Method to interpret the DTML
        code that it contains.  The method returns the result of the
        interpretation, which can be any kind of object.

        To accomplish its task, DTML Method often needs to resolve various
        names into objects.  For example, when the code '&lt;dtml-var
        spam&gt;' is executed, the DTML engine tries to resolve the name
        'spam'.

        In order to resolve names, the Method must be passed a
        namespace to look them up in.  This can be done several ways:

          * By passing a 'client' object -- If the argument 'client' is
            passed, then names are looked up as attributes on the
            argument.

          * By passing a 'REQUEST' mapping -- If the argument 'REQUEST'
            is passed, then names are looked up as items on the
            argument.  If the object is not a mapping, an TypeError
            will be raised when a name lookup is attempted.

          * By passing keyword arguments -- names and their values can
            be passed as keyword arguments to the Method.

        The namespace given to a DTML Method is the composite of
        these three methods.  You can pass any number of them or none
        at all. Names will be looked up first in the keyword argument,
        next in the client and finally in the mapping.

        Unlike DTMLDocuments, DTMLMethods do not look up names in
        their own instance dictionary.

        Passing in a namespace to a DTML Method is often referred to
        as providing the Method with a *context*.

        DTML Methods can be called three ways:

        From DTML

          A DTML Method can be called from another DTML Method or
          Document::

            <dtml-var standard_html_header>
              <dtml-var aDTMLMethod>
            <dtml-var standard_html_footer>

          In this example, the Method 'aDTMLMethod' is being called
          from another DTML object by name.  The calling method passes
          the value 'this' as the client argument and the current DTML
          namespace as the REQUEST argument.  The above is identical
          to this following usage in a DTML Python expression::

            <dtml-var standard_html_header>
              <dtml-var "aDTMLMethod(_.None, _)">
            <dtml-var standard_html_footer>

        From Python

          Products, External Methods, and Scripts can call a DTML
          Method in the same way as calling a DTML Method from a
          Python expression in DTML; as shown in the previous example.

        By the Publisher

          When the URL of a DTML Method is fetched from Zope, the DTML
          Method is called by the publisher.  The REQUEST object is
          passed as the second argument to the Method.

        Permission -- 'View'
        """

    def manage_edit(data, title):
        """
        Change the DTML Method, replacing its contents with 'data' and
        changing its title.

        The data argument may be a file object or a string.

        Permission -- 'Change DTML Methods'
        """

    def document_src():
        """
        Returns the unrendered source text of the DTML Method.

        Permission -- 'View management screens'
        """

    def get_size():
        """
        Returns the size of the unrendered source text of the DTML
        Method in bytes.

        Permission -- 'View'
        """

    __constructor__ = manage_addDTMLMethod
