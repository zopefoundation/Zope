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
"""Catalog 

A Catalog object provides an inteface to index objects.
"""

from Globals import HTMLFile, MessageDialog
from OFS.SimpleItem import Item
from Products.ZTablesCore import ZTablesCore
from SearchIndex import Query
import string, regex, urlparse

class Catalog(Item):
    """Catalog object"""

    meta_type = "Catalog"
    
    __ac_permissions__=(
        ('Manage Catalog Entries',
         ['indexObject', 
          'unindexObject',
          'indexAddColumn'], ['Manager']),
         ('Search SiteIndex',
          ['searchResults','__call__'],['Anonymous', 'Manager']), 
        )

    
    def __init__(self,id,title=None):
        self.id=id
        self.title=title
        self._ztable=ZTablesCore.ZTable(id)


        # them
        
        schema = [('id', 'FieldIndex', 's', None),
                  ('url', 'FieldIndex', 's', 1),
                  ('title', 'TextIndex', 's', None),
                  ('meta_type', 'FieldIndex', 's', None),
                  ('last_modified', 'FieldIndex', 'd', None),
                  ('subject', 'TextIndex', 's', None),
                  ('description', 'TextIndex', 's', None),
                  ('date', 'FieldIndex', 'd', None),
                  ('reviewed', 'FieldIndex', 'i', None),
                  ]

        uindex = []
        utype = []
        call = []
        for name, index, type, ci in schema:
            self._ztable.addColumn(name)
            uindex.append(index)
            utype.append(type)
            call.append(ci)

        # create an orphan index for text_content.  A table row will
        # not get created but an index will.

        self._ztable._data.setOrphanIndex('text_content', 'TextIndex',
        call_methods=1)

        self._ztable._data.addComputedField('modified_since',
                                            '(_.DateTime() - 1)',
                                            index_type='FieldIndex',
                                            type='d')

        self._ztable.update_database_schema(uindex, utype, call)


    def searchResults(self, REQUEST=None, used=None,
                      query_map={
                          type(regex.compile('')): Query.Regex,
                          type([]): ZTablesCore.orify,
                          type(''): Query.String,
                          }, **kw):
        """
        Search the catalog according to the ZTables search interface.
        Search terms can be passed in the REQUEST or as keyword
        arguments. 
        """
        return apply(self._ztable.searchResults,(REQUEST,used,query_map),kw)


    __call__ = searchResults

    

    def uniqueValuesFor(self, id):
        """ return unique values for field index id """
        return apply(self._ztable.uniqueValuesFor, (id,))


    def data_column_names(self):
        """
        Returns a list of all column names
        """
        return (list(self._ztable._data._names) + 
                self._ztable._data._computed_fields)



    def indexObject(self, obj, REQUEST=None):
        """ 
        Indexes a single object, either by creating new record, or 
        by updating an existing index for the object
        """

        # r_id is the record id in the table, *not* the object's 'id'.
        r = self._get_record(obj)
        r_id = self._obj2id(obj)

        if r_id is not None:
            self._ztable.editRecord(r_id, r, obj)

        else:
            self._ztable.addRecord(r, obj)

        if REQUEST is not None:
            return MessageDialog(title='Object Indexed',
                                 message='The object has been indexed.',
                                 action='manage_main')
            


    def unindexObject(self, obj, REQUEST=None):
        """Remove object from the Catalog. 

        """

        r_id = self._obj2id(obj)
        if r_id is not None:
            self._ztable.deleteRecord(r_id, obj)
        else:
            pass

        if REQUEST is not None:
            return MessageDialog(title='Catalog records deleted',
                    message='%s catalog records deleted.' % num,
                    action='manage_main')
    


    def indexAddColumn(self, name, type='s', index_type='FieldIndex'):
        """
        Adds an column and index to the catalog.
        'type' is a type code ['s'|'t'|'i'|'f'|'d'|'b']
        'index_type' is index type code:
        ['FieldIndex'|'TextIndex'|'KeywordIndex']

        Note: KeywordIndex is not yet supported in the ZTable Core
        """

        self._ztable.addColumn(name,type)
        self._ztable._getDataSet().setOneIndex(name,index_type)
    

    def _obj2id(self, obj):
        results=self._ztable.searchResults(url=obj.url())
        if results:
            return results[0].data_record_id_


    def _get_record(self, obj):
        """
        return a catalog record to be stored in the table for 'obj'.
        """
        record = {}
        record['id'] = callable(obj.id) and obj.id() or obj.id
        record['url'] = obj.url()
        record['title'] = obj.title
        record['last_modified'] = obj.bobobase_modification_time()
        record['meta_type'] = obj.meta_type

        if obj.meta_type in ['Document','DTML Document','DTML Method']:
            record['text_content']=obj.read_raw()

        record['subject'] = obj.subject
        record['description'] = obj.description
        record['summary'] = obj.summary
        record['reviewed'] = obj.reviewed

        return record

    









