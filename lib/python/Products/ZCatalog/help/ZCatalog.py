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


class ZCatalog:
    """

    ZCatalog object

    A ZCatalog contains arbitrary index like references to Zope
    objects.  ZCatalog's can index either 'Field' values of object,
    'Text' values, or 'KeyWord' values:

    Indexes

      Text -- XXX

      Field -- XXX

      Keyword -- XXX

    Meta-data

      XXX

    ZCatalog does not store references to the objects themselves, but
    rather to a unique identifier that defines how to get to the
    object.  In Zope, this unique identifier is the object's relative
    path to the ZCatalog (since two Zope object's cannot have the same 
    URL, this is an excellent unique qualifier in Zope).

    """

    def catalog_object(self, obj, uid):
        """

        Catalogs the object 'obj' with the unique identifier 'uid'.

        """

    def uncatalog_object(self, uid):
        """

        Uncatalogs the object with the unique identifier 'uid'.

        """

    def uniqueValuesFor(self, name):
        """

        returns the unique values for a given FieldIndex named 'name'.

        """

    def getpath(self, rid):
        """
        
        Return the path to a cataloged object given a
        'data_record_id_'
        
        """


    def getobject(self, rid, REQUEST=None):
        """
        
        Return a cataloged object given a 'data_record_id_'
        
        """

    def schema(self):
        """

        Returns a sequence of names that correspond to columns in the
        meta-data table.

        """

    def indexes(self):
        """

        Returns a sequence of names that correspond to indexes.

        """

    def index_objects(self):
        """

        Returns a sequence of actual index objects.

        """

    def searchResults(self, REQUEST=None, **kw):
        """
        
        Search the catalog.  Search terms can be passed in the REQUEST
        or as keyword arguments.

        
        XXX search grammar, how terms are combined, special search
        terms, format of returned results XXX

        """
    
    def __call__(self, REQUEST=None, **kw):
        """
        Search the catalog, the same way as 'searchResults'.
        """
