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


def manage_addDocument(self, id, title):
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
    
    def __call__(self, client=None, REQUEST={}, RESPONSE=None, **kw):
        """

        Calling a DTMLDocument causes the Document to interpret the DTML
        code that it contains.  The method returns the result of the
        interpretation, which can be any kind of object.

        To accomplish its task, DTML Document often needs to resolve various
        names into objects.  For example, when the code <dtml-var
        spam> is executed, the DTML engine tries to resolve the name
        'spam'.

        In order to resolve names, the Document must be passed a
        names pace to look them up in.  This can be done several ways:

          By passing a 'client' object -- If the argument 'client' is
            passed, then names are looked up as attributes on the
            argument.

          By passing a 'REQUEST' mapping -- If the argument 'REQUEST'
            is passed, then names are looked up as items on the
            argument.  If the object is not a mapping, an TypeError
            will be raised when a name lookup is attempted.

          By passing keyword arguments -- names and their values can
          be passed as keyword arguments to the Document.

        The names pace given to a DTML Document is the composite of these
        three methods.  You can pass any number of them or none at
        all.

        Passing in a names pace to a DTML Document is often referred to
        as providing the Document with a *context*.

        DTML Documents are called three ways:

          From DTML -- A DTML Document can be called from another DTML
            Method or Document::

              <dtml-var standard_html_header>
                <dtml-var aDTMLDocument>
              <dtml-var standard_html_footer>

            In this example, the Document 'aDTMLDocument' is being called
            from another DTML object by name.  The calling method
            passes the value 'this' as the client argument and the
            current DTML names pace as the REQUEST argument.  The above
            is identical to this following usage in a DTML Python
            expression::

              <dtml-var standard_html_header>
                <dtml-var "aDTMLDocument(_.None, _)">
              <dtml-var standard_html_footer>

          From Python -- Products, External Methods, and PythonMethods 
            can call a DTML Document in the same way as calling a DTML
            Document from a Python expression in DTML; as shown in the
            previous example.

          By the Publisher -- When the URL of a DTML Document is fetched 
            from Zope, the DTML Document is called by the publisher.
            The REQUEST object is passes as the second argument to the 
            Document.  More information on the REQUEST can be found "on
            the online Interface
            documentation.":http://www.zope.org/Members/michel/Projects/Interfaces/PublisherRequest
          
        Permission -- 'View'

        """

    def manage_edit(self, data, title):
        """
        Change the DTML Document, replacing its contents with 'data'
        and
        changing its title.
        
        The data argument may be a file object or a string.
        
        Permission -- 'Change DTML Documents'
        """
        
    def document_src(self):
        """
        Returns the unrendered source text of the DTML Document.
        
        Permission -- 'View management screens'
        """
        
    def get_size(self):
        """
        Returns the size of the unrendered source text of the DTML
        Document in bytes.
        
        """

    __constructor__=manage_addDocument


