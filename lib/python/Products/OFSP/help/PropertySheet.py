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

class PropertySheet:
    """

    A PropertySheet is an abstraction for organizing and working
    with a set of related properties. Conceptually it acts like a
    container for a set of related properties and meta-data describing 
    those properties. A PropertySheet may or may not provide a web 
    interface for managing its properties.

    """

    def xml_namespace(self):
        """

        Return a namespace string usable as an xml namespace
        for this property set. This may be an empty string if 
        there is no default namespace for a given property sheet
        (especially property sheets added in ZClass definitions).

        Permission -- XXX

        """

    def getProperty(self, id, d=None):
        """

        Get the property 'id', returning the optional second 
        argument or None if no such property is found.

        Permission -- XXX
        
        """

    def getPropertyType(self, id):
        """
        
        Get the type of property 'id'. Returns None if no such
        property exists.

        Permission -- XXX
        
        """

    def hasProperty(self, id):
        """

        Returns true if 'self' has a property with the given 'id', 
        false otherwise.

        Permission -- 'Access contents information'

        """

    def propertyIds(self):
        """

        Returns a list of property ids.

        Permission --  'Access contents information'

        """

    def propertyValues(self):
        """

        Returns a list of actual property values.

        Permission -- 'Access contents information'

        """

    def propertyItems(self):
        """

        Return a list of (id, property) tuples.

        Permission -- 'Access contents information'

        """
        
    def propertyMap(self):
        """

        Returns a tuple of mappings, giving meta-data for properties.

        Perimssion -- XXX

        """

    def propertyInfo(self):
        """

        Returns a mapping containing property meta-data.

        Permission -- XXX

        """

    def manage_addProperty(self, id, value, type, REQUEST=None):
        """

        Add a new property with the given 'id', 'value' and 'type'.

        Property Types

           XXX

        This method will use the passed in 'type' to try to convert
        the 'value' argument to the named type. If the given 'value'
        cannot be converted, a ValueError will be raised.

        *If the given 'type' is not recognized, the 'value' and 'type'
        given are simply stored blindly by the object. This seems like
        bad behavior - it should probably raise an exception instead.*

        If no value is passed in for 'REQUEST', the method will return
        'None'. If a value is provided for 'REQUEST' (as it will when
        called via the web), the property management form for the
        object will be rendered and returned.

        This method may be called via the web, from DTML or from
        Python code.

        Permission -- 'Manage Properties'

        """

    def manage_changeProperties(self, REQUEST=None, **kw):
        """

        Change existing object properties by passing either a mapping 
        object as 'REQUEST' containing name:value pairs or by passing 
        name=value keyword arguments.

        Some objects have "special" properties defined by product 
        authors that cannot be changed. If you try to change one of 
        these properties through this method, an error will be raised.

        Note that no type checking or conversion happens when this 
        method is called, so it is the caller's responsibility to 
        ensure that the updated values are of the correct type. 
        *This should probably change*.

        If a value is provided for 'REQUEST' (as it will be when
        called via the web), the method will return an HTML message
        dialog. If no REQUEST is passed, the method returns 'None' on
        success.

        This method may be called via the web, from DTML or from
        Python code.

        Permission - 'Manage Properties'

        """


    def manage_delProperties(self, ids=None, REQUEST=None):
        """

        Delete one or more properties with the given 'ids'. The 'ids' 
        argument should be a sequence (tuple or list) containing the 
        ids of the properties to be deleted. If 'ids' is empty no 
        action will be taken. If any of the properties named in 'ids' 
        does not exist, an error will be raised. 

        Some objects have "special" properties defined by product
        authors that cannot be deleted. If one of these properties is
        named in 'ids', an HTML error message is returned (this is
        lame and should be changed).

        If no value is passed in for 'REQUEST', the method will return
        None. If a value is provided for 'REQUEST' (as it will be when
        
        called via the web), the property management form for the
        object will be rendered and returned.

        This method may be called via the web, from DTML or from
        Python code.

        Permission - 'Manage Properties'

        """







