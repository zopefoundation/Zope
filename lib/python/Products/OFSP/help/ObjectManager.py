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

class ObjectManager:
    """
    An ObjectManager contains other Zope objects. The contained
    objects are Object Manager Items.
    """

    def objectIds(self, type=None):
        """
        This method returns a list of the ids of the contained
        objects.
        
        Optionally, you can pass an argument specifying what object
        meta_type(es) to restrict the results to. This argument can be
        a string specifying one meta_type, or it can be a list of
        strings to specify many.

        Example::

          <dtml-in objectIds>
            <dtml-var sequence-item>
          <dtml-else>
            There are no sub-objects.
          </dtml-in>

        This DTML code will display all the ids of the objects
        contained in the current Object Manager.

        Permission -- 'Access contents information'
        """

    def objectValues(self, type=None):
        """
        This method returns a sequence of contained objects.
        
        Like objectValues and objectIds, it accepts one argument,
        either a string or a list to restrict the results to objects
        of a given meta_type or set of meta_types.

        Example::

          <dtml-in "objectValues('Folder')">
            <dtml-var icon>
            This is the icon for the: <dtml-var id> Folder<br>.
          <dtml-else>
            There are no Folders.
          </dtml-in>

        The results were restricted to Folders by passing a 
        meta_type to 'objectItems' method.
        
        Permission -- 'Access contents information'
        """

    def objectItems(self, type=None):
        """
        This method returns a sequence of (id, object) tuples.
        
        Each tuple's first element is the id of an object contained in
        the Object Manager, and the second element is the object
        itself.
        
        Example::

          <dtml-in objectItems>
           id: <dtml-var sequence-key>,
           type: <dtml-var meta_type>
          <dtml-else>
            There are no sub-objects.
          </dtml-in>
          
        Permission -- 'Access contents information'
        """

    def superValues(self, t):
        """
        This method returns a list of objects of a given meta_type(es)
        contained in the Object Manager and all its parent Object
        Managers.
        
        The t argument specifies the meta_type(es). It can be a string
        specifying one meta_type, or it can be a list of strings to
        specify many.
        
        Permission -- Python only
        """
