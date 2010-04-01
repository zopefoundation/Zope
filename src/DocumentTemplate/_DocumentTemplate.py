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
'''Document templates with fill-in fields

Document templates provide for creation of textual documents, such as
HTML pages, from template source by inserting data from python objects
and name-spaces.

When a document template is created, a collection of default values to
be inserted may be specified with a mapping object and with keyword
arguments.

A document templated may be called to create a document with values
inserted.  When called, an instance, a mapping object, and keyword
arguments may be specified to provide values to be inserted.  If an
instance is provided, the document template will try to look up values
in the instance using getattr, so inheritence of values is supported.
If an inserted value is a function, method, or class, then an attempt
will be made to call the object to obtain values.  This allows
instance methods to be included in documents.

Document templates masquerade as functions, so the python object
publisher (Bobo) will call templates that are stored as instances of
published objects. Bobo will pass the object the template was found in
and the HTTP request object.

Two source formats are supported:

   Extended Python format strings (EPFS) --
      This format is based on the insertion by name format strings
      of python with additional format characters, '[' and ']' to
      indicate block boundaries.  In addition, parameters may be
      used within formats to control how insertion is done.

      For example:

         %%(date fmt=DayOfWeek upper)s

      causes the contents of variable 'date' to be inserted using
      custom format 'DayOfWeek' and with all lower case letters
      converted to upper case.

   HTML --
      This format uses HTML server-side-include syntax with
      commands for inserting text. Parameters may be included to
      customize the operation of a command.

      For example:

         <!--#var total fmt=12.2f-->

      is used to insert the variable 'total' with the C format
      '12.2f'.

Document templates support conditional and sequence insertion

    Document templates extend python string substitition rules with a
    mechanism that allows conditional insertion of template text and that
    allows sequences to be inserted with element-wise insertion of
    template text.

Access Control

    Document templates provide a basic level of access control by
    preventing access to names beginning with an underscore.
    Additional control may be provided by providing document templates
    with a 'guarded_getattr' and 'guarded_getitem' method.  This would
    typically be done by subclassing one or more of the DocumentTemplate
    classes.

    If provided, the the 'guarded_getattr' method will be called when
    objects are accessed as instance attributes or when they are
    accessed through keyed access in an expression.

Document Templates may be created 4 ways:

    DocumentTemplate.String -- Creates a document templated from a
        string using an extended form of python string formatting.

    DocumentTemplate.File -- Creates a document templated bound to a
        named file using an extended form of python string formatting.
        If the object is pickled, the file name, rather than the file
        contents is pickled.  When the object is unpickled, then the
        file will be re-read to obtain the string.  Note that the file
        will not be read until the document template is used the first
        time.

    DocumentTemplate.HTML -- Creates a document templated from a
        string using HTML server-side-include rather than
        python-format-string syntax.

    DocumentTemplate.HTMLFile -- Creates an HTML document template
        from a named file.

'''


__version__='$Revision: 1.14 $'[11:-2]

from DocumentTemplate.DT_Raise import ParseError
from DocumentTemplate.DT_String import String, File
from DocumentTemplate.DT_HTML import HTML, HTMLFile, HTMLDefault

# import DT_UI # Install HTML editing
