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

def manage_addImage(id, file, title='', precondition='', content_type=''):
    """

    Add a new Image object.

    Creates a new Image object 'id' with the contents of 'file'.

    """



class Image:
    """
    An Image is a Zope object that contains image content.  An Image
    object can be used to upload or download image information with
    Zope.

    Image objects have two properties the define their dimension,
    'height' and 'width'. These are calculated when the image is
    uploaded. For image types that Zope does not understand, these
    properties may be undefined.

    Using a Image object in Zope is easy.  The most common usage is
    to display the contents of an image object in a web page.  This
    is done by simply referencing the object from DTML::

      <dtml-var standard_html_header>
        <dtml-var ImageObject>
      <dtml-var standard_html_footer>

    This will generate an HTML IMG tag referencing the URL to the
    Image. This is equivalent to::

      <dtml-var standard_html_header>
        <dtml-with ImageObject>
          <img src="<dtml-var absolute_url>">
        </dtml-with>
      <dtml-var standard_html_footer>

    You can control the image display more precisely with the 'tag'
    method. For example::

      <dtml-var "ImageObject.tag(border='5', align='left')">

    """

    __constructor__=manage_addImage

    __extends__=('OFSP.File.File',)

    def tag(height=None, width=None, alt=None,
            scale=0, xscale=0, yscale=0, **args):
        """
        This method returns a string which contains an HTML IMG tag
        reference to the image.

        Optionally, the 'height', 'width', 'alt', 'scale', 'xscale'
        and 'yscale' arguments can be provided which are turned into
        HTML IMG tag attributes. Note, 'height' and 'width' are
        provided by default, and 'alt' comes from the 'title'
        property.

        Keyword arguments may be provided to support other or future IMG
        tag attributes.  The one exception to this is the HTML Cascading
        Style Sheet tag 'class'.  Because the word 'class' is a reserved
        keyword in Python, you must instead use the keyword argument
        'css_class'.  This will be turned into a 'class' HTML tag attribute
        on the rendered 'img' tag.

        Permission -- 'View'
        """
