##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
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
    with a 'read_guard' method.  This would typically be done by
    subclassing one or more of the DocumentTemplate classes.

    If provided, the the 'read_guard' method will be called when objects
    are accessed as accessed as instance attributes or when they are
    accessed through keyed access in an expression..  The 'read_guard'
    method will be called with the containing object.  It can
    return a wrapper object from which the attribute will be accessed.

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


__version__='$Revision: 1.11 $'[11:-2]

ParseError='Document Template Parse Error'

from DT_String import String, File
from DT_HTML import HTML, HTMLFile, HTMLDefault
# import DT_UI # Install HTML editing
