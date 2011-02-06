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


def manage_addFile(id, file='', title='', precondition='', content_type=''):
    """

    Add a new File object.

    Creates a new File object 'id' with the contents of 'file'

    """

class File:
    """
    A File is a Zope object that contains file content.  A File object
    can be used to upload or download file information with Zope.

    Using a File object in Zope is easy.  The most common usage is
    to display the contents of a file object in a web page.  This is
    done by simply referencing the object from DTML::

      <dtml-var standard_html_header>
        <dtml-var FileObject>
      <dtml-var standard_html_footer>

    A more complex example is presenting the File object for
    download by the user.  The next example displays a link to every
    File object in a folder for the user to download::

      <dtml-var standard_html_header>
      <ul>
        <dtml-in "ObjectValues('File')">
          <li><a href="<dtml-var absolute_url>"><dtml-var
          id></a></li>
        </dtml-in>
      </ul>
      <dtml-var standard_html_footer>

    In this example, the 'absolute_url' method and 'id' are used to
    create a list of HTML hyperlinks to all of the File objects in
    the current Object Manager.

    Also see ObjectManager for details on the 'objectValues'
    method.
    """

    __constructor__=manage_addFile

    __extends__=(
        'OFSP.ObjectManagerItem.ObjectManagerItem',
        'OFSP.PropertyManager.PropertyManager',
        )

    def update_data(data, content_type=None, size=None):
        """
        Updates the contents of the File with 'data'.

        The 'data' argument must be a string. If 'content_type' is not
        provided, then a content type will not be set. If size is not
        provided, the size of the file will be computed from 'data'.

        Permission -- Python only
        """

    def getSize():
        """
        Returns the size of the file in bytes.

        Permission -- 'View'
        """

    def getContentType():
        """
        Returns the content type of the file.

        Permission -- 'View'
        """
