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

class ObjectManagerItem:
    """
    A Zope object that can be contained within an Object Manager.
    Almost all Zope objects that can be managed through the web are
    Object Manager Items.

    Attributes
         
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
        Return the absolute url to the object.

        If the relative argument is provided with a true value, then
        the URL returned is relative to the site object. Note, if
        virtual hosts are being used, then the path returned is a
        logical, rather than a physical path.
        
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

        Permission -- Python only

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

        Permission -- Python only
        """


    
