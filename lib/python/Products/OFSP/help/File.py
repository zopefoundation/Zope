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


def manage_addFile(self,id,file='',title='',precondition='', content_type=''):
    """

    Add a new File object.

    Creates a new File object 'id' with the contents of 'file'

    """

class File:
    """
    A File is a Zope object that contains file content.  A File object
    can be used to upload or download file information with Zope.

    Examples:

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
    
    def update_data(self, data, content_type=None, size=None):
        """
        Updates the contents of the File with 'data'.
        
        The 'data' argument must be a string. If 'content_type' is not
        provided, then a content type will not be set. If size is not
        provided, the size of the file will be computed from 'data'.
        
        Permission -- Python only
        """

    def getSize(self):
        """
        Returns the size of the file in bytes.
        
        Permission -- 'View'
        """

    def getContentType(self):
        """
        Returns the content type of the file.
        
        Permission -- 'View'
        """
