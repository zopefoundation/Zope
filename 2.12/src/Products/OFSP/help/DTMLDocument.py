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


def manage_addDocument(id, title):
    """
    Add a DTML Document to the current ObjectManager
    """


class DTMLDocument:
    """
    A DTML Document is a Zope object that contains and executes DTML
    code. It is useful to represent web pages.
    """

    __extends__=(
        'OFSP.ObjectManagerItem.ObjectManagerItem',
        'OFSP.PropertyManager.PropertyManager',
        )

    def __call__(client=None, REQUEST={}, RESPONSE=None, **kw):
        """

        Calling a DTMLDocument causes the Document to interpret the DTML
        code that it contains.  The method returns the result of the
        interpretation, which can be any kind of object.

        To accomplish its task, DTML Document often needs to resolve various
        names into objects.  For example, when the code '&lt;dtml-var
        spam&gt;' is executed, the DTML engine tries to resolve the name
        'spam'.

        In order to resolve names, the Document must be passed a
        namespace to look them up in.  This can be done several ways:

          * By passing a 'client' object -- If the argument 'client' is
            passed, then names are looked up as attributes on the
            argument.

          * By passing a 'REQUEST' mapping -- If the argument 'REQUEST'
            is passed, then names are looked up as items on the
            argument.  If the object is not a mapping, an TypeError
            will be raised when a name lookup is attempted.

          * By passing keyword arguments -- names and their values can
            be passed as keyword arguments to the Document.

        The namespace given to a DTML Document is the composite of
        these three methods.  You can pass any number of them or none
        at all. Names are looked up first in the keyword arguments,
        then in the client, and finally in the mapping.

        A DTMLDocument implicitly pass itself as a client argument in
        addition to the specified client, so names are looked up in
        the DTMLDocument itself.

        Passing in a namespace to a DTML Document is often referred to
        as providing the Document with a *context*.

        DTML Documents can be called three ways.

        From DTML

          A DTML Document can be called from another DTML
          Method or Document::

            <dtml-var standard_html_header>
              <dtml-var aDTMLDocument>
            <dtml-var standard_html_footer>

          In this example, the Document 'aDTMLDocument' is being called
          from another DTML object by name.  The calling method
          passes the value 'this' as the client argument and the
          current DTML namespace as the REQUEST argument.  The above
          is identical to this following usage in a DTML Python
          expression::

            <dtml-var standard_html_header>
              <dtml-var "aDTMLDocument(_.None, _)">
            <dtml-var standard_html_footer>

        From Python

          Products, External Methods, and Scripts can call a DTML
          Document in the same way as calling a DTML Document from a
          Python expression in DTML; as shown in the previous example.

        By the Publisher

          When the URL of a DTML Document is fetched from Zope, the
          DTML Document is called by the publisher.  The REQUEST
          object is passed as the second argument to the Document.

        Permission -- 'View'

        """

    def manage_edit(data, title):
        """
        Change the DTML Document, replacing its contents with 'data'
        and
        changing its title.

        The data argument may be a file object or a string.

        Permission -- 'Change DTML Documents'
        """

    def document_src():
        """
        Returns the unrendered source text of the DTML Document.

        Permission -- 'View management screens'
        """

    def get_size():
        """
        Returns the size of the unrendered source text of the DTML
        Document in bytes.

        Permission -- 'View'
        """

    __constructor__=manage_addDocument
