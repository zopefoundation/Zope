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
"""ZCatalog product"""

from Globals import HTMLFile, MessageDialog
import Globals
from OFS.Folder import Folder
from OFS.FindSupport import FindSupport
from DateTime import DateTime
from SearchIndex import Query
import string, regex, urlparse, urllib, os, sys
import Products
from Acquisition import Implicit
from Persistence import Persistent
from Catalog import Catalog, orify
from SearchIndex import UnIndex, UnTextIndex
import IOBTree

manage_addZCatalogForm=HTMLFile('addZCatalog',globals())

def manage_addZCatalog(self,id,title,REQUEST=None):
        """Add a ZCatalog object
        """
        c=ZCatalog(id,title)
        self._setObject(id,c)
        if REQUEST is not None:
                return self.manage_main(self,REQUEST)


class ZCatalog(Folder, FindSupport, Persistent, Implicit):
    """ZCatalog object

    A ZCatalog contains arbirary index like references to Zope
    objects.  ZCatalog's can index either 'Field' values of object, or 
    'Text' values.

    ZCatalog does not store references to the objects themselves, but
    rather to a unique identifier that defines how to get to the
    object.  In Zope, this unique idenfier is the object's relative
    path to the ZCatalog (since two Zope object's cannot have the same 
    URL, this is an excellent unique qualifier in Zope).

    Most of the dirty work is done in the _catalog object, which is an
    instance of the Catalog class.  An interesting feature of this
    class is that it is not Zope specific.  You can use it in any
    Python program to catalog objects.

    """

    meta_type = "ZCatalog"
    icon='misc_/ZCatalog/ZCatalog.gif'
    
    manage_options=(
            
        {'label': 'Contents', 'action': 'manage_main',
         'target': 'manage_main'},
        {'label': 'Cataloged Objects', 'action': 'manage_catalogView',
         'target': 'manage_main'},
        {'label': 'Find Items to ZCatalog', 'action': 'manage_catalogFind', 
         'target':'manage_main'},
        {'label': 'MetaData Table', 'action': 'manage_catalogSchema', 
         'target':'manage_main'},
        {'label': 'Indexes', 'action': 'manage_catalogIndexes', 
         'target':'manage_main'},
        {'label': 'Status', 'action': 'manage_catalogStatus', 
         'target':'manage_main'},
        )

    __ac_permissions__=(

        ('Manage ZCatalog Entries',
         ['manage_catalogObject', 'manage_uncatalogObject',
          'catalog_object', 'uncatalog_object',
          
          'manage_catalogView', 'manage_catalogFind',
          'manage_catalogSchema', 'manage_catalogIndexes',
          'manage_catalogStatus',
          
          'manage_catalogReindex', 'manage_catalogFoundItems',
          'manage_catalogClear', 'manage_addColumn', 'manage_delColumns',
          'manage_addIndex', 'manage_delIndexs', 'manage_main',], 
         ['Manager']),

         ('Search ZCatalog',
          ['searchResults', '__call__', 'uniqueValuesFor',
           'getpath', 'schema', 'indexes', 'index_objects',
           'all_meta_types', 'valid_roles', 'resolve_url',
           'getobject'],
          ['Anonymous', 'Manager']), 
        )


    manage_catalogAddRowForm = HTMLFile('catalogAddRowForm', globals())
    manage_catalogView = HTMLFile('catalogView',globals())
    manage_catalogFind = HTMLFile('catalogFind',globals())
    manage_catalogSchema = HTMLFile('catalogSchema', globals())
    manage_catalogIndexes = HTMLFile('catalogIndexes', globals())
    manage_catalogStatus = HTMLFile('catalogStatus', globals())

    def __init__(self,id,title=''):
        self.id=id
        self.title=title
        self.threshold = 1000
        self._v_total = 0
        self._catalog = Catalog()

        self._catalog.addColumn('id')
        self._catalog.addIndex('id', 'FieldIndex')

        self._catalog.addColumn('title')
        self._catalog.addIndex('title', 'TextIndex')

        self._catalog.addColumn('meta_type')
        self._catalog.addIndex('meta_type', 'FieldIndex')

        self._catalog.addColumn('bobobase_modification_time')
        self._catalog.addIndex('bobobase_modification_time', 'FieldIndex')

        self._catalog.addColumn('summary')
        self._catalog.addIndex('PrincipiaSearchSource', 'TextIndex')
        
    def manage_edit(self, threshold=1000, REQUEST=None):
        """ edit the catalog """
        self.threshold = threshold

        message = "Object changed"
        return self.manage_main(self, REQUEST,
                                manage_tabs_message=message)

    def manage_catalogObject(self, REQUEST, urls=None):
        """ index all Zope objects that 'urls' point to """
        if urls:
            for url in urls:
                try:
                    # if an error happens here, the catalog will be in
                    # an unstable state.  If this happens, ignore the
                    # object.
                    obj = self.resolve_url(url, REQUEST)
                except:
                    continue
                
                self.catalog_object(obj, url)

        message = "Objects Cataloged"
        return self.manage_main(self, REQUEST,
                                manage_tabs_message=message)

    def manage_uncatalogObject(self, REQUEST, urls=None):
        """ removes Zope object 'urls' from catalog """
##	import pdb
##	pdb.set_trace()
        if urls:
            for url in urls:
                try:
                    obj = self.resolve_url(url, REQUEST)
                except:
                    continue
                self.uncatalog_object(url)

        message = "Object UnCataloged"
        return self.manage_main(self, REQUEST,
                                manage_tabs_message=message)

    def manage_catalogReindex(self, REQUEST):
        """ clear the catalog, then re-index everything """
	
        paths = tuple(self._catalog.paths.values())
	self.manage_catalogClear(REQUEST)

	for p in paths:
	    try:
		obj = self.resolve_url(p, REQUEST)
		self.catalog_object(obj, p)		
	    except:
		pass
		

##        for path, i in items:
##            try:
##                obj = self.getobject(i, REQUEST)
##            except:
##                self.uncatalog_object(path)
##            else:
##                self.uncatalog_object(path)
##                self.catalog_object(obj, path)

        message = "Catalog Reindexed"
        return self.manage_catalogView(self, REQUEST,
                                manage_tabs_message=message)

    def manage_catalogClear(self, REQUEST):
        """ clears the whole enchelada """
        self._catalog.clear()

        message = "Catalog Cleared"
        return self.manage_main(self, REQUEST,
                                manage_tabs_message=message)

    def manage_catalogFoundItems(self, REQUEST, obj_metatypes=None,
                                 obj_ids=None, obj_searchterm=None,
                                 obj_expr=None, obj_mtime=None,
                                 obj_mspec=None, obj_roles=None,
                                 obj_permission=None):
    
        """ Find object according to search criteria and Catalog them
        """
        results = self.ZopeFind(REQUEST.PARENTS[1],
                                obj_metatypes=obj_metatypes,
                                obj_ids=obj_ids,
                                obj_searchterm=obj_searchterm,
                                obj_expr=obj_expr,
                                obj_mtime=obj_mtime,
                                obj_mspec=obj_mspec,
                                obj_permission=obj_permission,
                                obj_roles=obj_roles,
                                search_sub=1,
                                REQUEST=REQUEST)

        for n in results:
            self.catalog_object(n[1], n[0])

        message = "Objects Cataloged"
        return self.manage_catalogView(self, REQUEST,
                                manage_tabs_message=message)

    def manage_addColumn(self, name, REQUEST):
        """ add a column """
        self._catalog.addColumn(name)

        message = "Column added"
        return self.manage_catalogSchema(self, REQUEST,
                                          manage_tabs_message=message)

    def manage_delColumns(self, names, REQUEST):
        """ del a column """
        for name in names:
            self._catalog.delColumn(name)
            
        message = "Columns deleted"
        return self.manage_catalogSchema(self, REQUEST,
                                          manage_tabs_message=message)

    def manage_addIndex(self, name, type, REQUEST):
        """ add an index """
        self._catalog.addIndex(name, type)
        
        message = "Index added"
        return self.manage_catalogIndexes(self, REQUEST,
                                          manage_tabs_message=message)

    def manage_delIndexes(self, names, REQUEST):
        """ del an index """
        for name in names:
            self._catalog.delIndex(name)

        message = "Indexes deleted"
        return self.manage_catalogIndexes(self, REQUEST,
                                          manage_tabs_message=message)
    
    def catalog_object(self, obj, uid):
        """ wrapper around catalog """
        if not hasattr(self, '_v_total'):
            self._v_total = 0
        self._v_total = (self._v_total +
                         self._catalog.catalogObject(obj, uid, self.threshold))
        
        if self._v_total > self.threshold:
            get_transaction().commit(1)
            self._v_total = 0

    def uncatalog_object(self, uid):
        """ wrapper around catalog """
        self._catalog.uncatalogObject(uid)

    def uniqueValuesFor(self, name):
        """ returns the unique values for a given FieldIndex """
        return self._catalog.uniqueValuesFor(name)

    def getpath(self, rid):
        """
        Return the path to a cataloged object given a 'data_record_id_'
        """
        return self._catalog.paths[rid]

    def getobject(self, rid, REQUEST=None):
        """
        Return a cataloged object given a 'data_record_id_'
        """
        if REQUEST is None:
            REQUEST=self.REQUEST
	try:
	    obj = self.resolve_url(self.getpath(rid), REQUEST)
	except:
	    return None
        return obj

    def schema(self):
        return self._catalog.schema.keys()

    def indexes(self):
        return self._catalog.indexes.keys()

    def index_objects(self):
        return self._catalog.indexes.values()

    def _searchable_arguments(self):
        r = {}
        n={'optional':1}
        for name in self._catalog.indexes.keys():
            r[name]=n
        return r

    def _searchable_result_columns(self):
        r = []
        for name in self._catalog.indexes.keys():
            i = {}
            i['name'] = name
            i['type'] = 's'
            i['parser'] = str
            i['width'] = 8
            r.append(i)
        return r

    def searchResults(self, REQUEST=None, used=None,
                      query_map={
                          type(regex.compile('')): Query.Regex,
                          type([]): orify,
                          type(''): Query.String,
                          }, **kw):
        """
        Search the catalog according to the ZTables search interface.
        Search terms can be passed in the REQUEST or as keyword
        arguments. 
        """
        
        return apply(self._catalog.searchResults,
                     (REQUEST,used, query_map), kw)

    __call__=searchResults

## this stuff is so the find machinery works

    meta_types=() # Sub-object types that are specific to this object
    
    def all_meta_types(self):
        pmt=()
        if hasattr(self, '_product_meta_types'): pmt=self._product_meta_types
        elif hasattr(self, 'aq_acquire'):
            try: pmt=self.aq_acquire('_product_meta_types')
            except:  pass
        return self.meta_types+Products.meta_types+pmt

    def valid_roles(self):
        "Return list of valid roles"
        obj=self
        dict={}
        dup =dict.has_key
        x=0
        while x < 100:
            if hasattr(obj, '__ac_roles__'):
                roles=obj.__ac_roles__
                for role in roles:
                    if not dup(role):
                        dict[role]=1
            if not hasattr(obj, 'aq_parent'):
                break
            obj=obj.aq_parent
            x=x+1
        roles=dict.keys()
        roles.sort()
        return roles

## stolen from ZPublisher and modified slightly
## Note: do not use, this method is depricated.  Use 'getobject'
    
    def resolve_url(self, path, REQUEST):
        """ The use of this function is depricated.  Use 'getobject' """
        # Attempt to resolve a url into an object in the Zope
        # namespace. The url must be a fully-qualified url. The
        # method will return the requested object if it is found
        # or raise the same HTTP error that would be raised in
        # the case of a real web request. If the passed in url
        # does not appear to describe an object in the system
        # namespace (e.g. the host, port or script name dont
        # match that of the current request), a ValueError will
        # be raised.

        while path and path[0]=='/':  path=path[1:]
        while path and path[-1]=='/': path=path[:-1]
        req=REQUEST.clone()
        rsp=req.response
        req['PATH_INFO']=path
        object=None
        try: object=req.traverse(path)
        except: rsp.exception(0)
        if object is not None:
            # waaa - traversal may return a "default object"
            # like an index_html document, though you really
            # wanted to get a Folder back :(

            if hasattr(object, 'id'):
                if callable(object.id):
                    name=object.id()
                else: name=object.id
            elif hasattr(object, '__name__'):
                name=object.__name__
            else: name=''
                
            if name != os.path.split(path)[-1]:
                result = req.PARENTS[0]
                req.close()
                return result
            req.close()
            return object
        req.close()
        raise rsp.errmsg, sys.exc_value


Globals.default__class_init__(ZCatalog)



