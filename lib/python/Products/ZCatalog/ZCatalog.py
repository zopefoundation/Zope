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
import string, regex, urlparse, urllib, os, sys, time
import Products
from Acquisition import Implicit
from Persistence import Persistent
from DocumentTemplate.DT_Util import InstanceDict, TemplateDict
from DocumentTemplate.DT_Util import Eval, expr_globals
from AccessControl.Permission import name_trans
from Catalog import Catalog, orify
from SearchIndex import UnIndex, UnTextIndex
from Vocabulary import Vocabulary
import IOBTree
from AccessControl import getSecurityManager


manage_addZCatalogForm=HTMLFile('addZCatalog',globals())

def manage_addZCatalog(self, id, title, vocab_id=None, REQUEST=None):
    """Add a ZCatalog object
    """
    id=str(id)
    title=str(title)
    vocab_id=str(vocab_id)
    if vocab_id == 'create_default_catalog_':
        vocab_id = None
        
    c=ZCatalog(id, title, vocab_id, self)
    self._setObject(id, c)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST)


class ZCatalog(Folder, Persistent, Implicit):
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

    manage_options=Folder.manage_options + (  
        {'label': 'Cataloged Objects', 'action': 'manage_catalogView',
         'target': 'manage_main',
         'help':('ZCatalog','ZCatalog_Cataloged-Objects.stx')},
        {'label': 'Find Items to ZCatalog', 'action': 'manage_catalogFind', 
         'target':'manage_main',
         'help':('ZCatalog','ZCatalog_Find-Items-to-ZCatalog.stx')},
        {'label': 'MetaData Table', 'action': 'manage_catalogSchema', 
         'target':'manage_main',
         'help':('ZCatalog','ZCatalog_MetaData-Table.stx')},
        {'label': 'Indexes', 'action': 'manage_catalogIndexes', 
         'target':'manage_main',
         'help':('ZCatalog','ZCatalog_Indexes.stx')},
        {'label': 'Status', 'action': 'manage_catalogStatus', 
         'target':'manage_main',
         'help':('ZCatalog','ZCatalog_Status.stx')},
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
          'manage_addIndex', 'manage_delIndexes', 'manage_main',], 
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


    threshold=10000
    _v_total=0

    def __init__(self, id, title='', vocab_id=None, container=None):
        self.id=id
        self.title=title
        self.vocab_id = vocab_id
        
        self.threshold = 10000
        self._v_total = 0

        if vocab_id is None:
            v = Vocabulary('Vocabulary', 'Vocabulary', globbing=1)
            self._setObject('Vocabulary', v)
            v = 'Vocabulary'
        else:
            v = vocab_id

        self._catalog = Catalog(vocabulary=v)

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


    def getVocabulary(self):
        """ more ack! """
        return getattr(self, self.vocab_id)


    def manage_edit(self, RESPONSE, URL1, threshold=1000, REQUEST=None):
        """ edit the catalog """
        if type(threshold) is not type(1):
            threshold=string.atoi(threshold)
        self.threshold = threshold

        RESPONSE.redirect(URL1 + '/manage_main?manage_tabs_message=Catalog%20Changed')


    def manage_subbingToggle(self, REQUEST, RESPONSE, URL1):
        """ toggle subtransactions """
        if self.threshold:
            self.threshold = None
        else:
            self.threshold = 10000
        
        RESPONSE.redirect(URL1 + '/manage_catalogStatus?manage_tabs_message=Catalog%20Changed')      


    def manage_catalogObject(self, REQUEST, RESPONSE, URL1, urls=None):
        """ index all Zope objects that 'urls' point to """
        if urls:
            for url in urls:
                obj = self.resolve_url(url, REQUEST)
                if obj is not None: 
                    self.catalog_object(obj, url)

        RESPONSE.redirect(URL1 + '/manage_catalogView?manage_tabs_message=Object%20Cataloged')


    def manage_uncatalogObject(self, REQUEST, RESPONSE, URL1, urls=None):
        """ removes Zope object 'urls' from catalog """

        if urls:
            for url in urls:
                self.uncatalog_object(url)

        RESPONSE.redirect(URL1 + '/manage_catalogView?manage_tabs_message=Object%20Uncataloged')


    def manage_catalogReindex(self, REQUEST, RESPONSE, URL1):
        """ clear the catalog, then re-index everything """

        elapse = time.time()
        c_elapse = time.clock()
        
        paths = tuple(self._catalog.paths.values())
        self._catalog.clear()

        for p in paths:
            obj = self.resolve_url(p, REQUEST)
            if obj is not None:
                self.catalog_object(obj, p)             

        elapse = time.time() - elapse
        c_elapse = time.clock() - c_elapse
        
        RESPONSE.redirect(URL1 + '/manage_catalogView?manage_tabs_message=' +
                          urllib.quote('Catalog Updated<br>Total time: %s<br>Total CPU time: %s' % (`elapse`, `c_elapse`)))
        

    def manage_catalogClear(self, REQUEST=None, RESPONSE=None, URL1=None):
        """ clears the whole enchelada """
        self._catalog.clear()

        if REQUEST and RESPONSE:
            RESPONSE.redirect(URL1 + '/manage_catalogView?manage_tabs_message=Catalog%20Cleared')


    def manage_catalogFoundItems(self, REQUEST, RESPONSE, URL2, URL1,
                                 obj_metatypes=None,
                                 obj_ids=None, obj_searchterm=None,
                                 obj_expr=None, obj_mtime=None,
                                 obj_mspec=None, obj_roles=None,
                                 obj_permission=None):
    
        """ Find object according to search criteria and Catalog them
        """

        elapse = time.time()
        c_elapse = time.clock()
        
        words = 0
        path=urllib.unquote(string.split(URL2, REQUEST.script)[1])
        
        results = self.ZopeFindAndApply(REQUEST.PARENTS[1],
                                        obj_metatypes=obj_metatypes,
                                        obj_ids=obj_ids,
                                        obj_searchterm=obj_searchterm,
                                        obj_expr=obj_expr,
                                        obj_mtime=obj_mtime,
                                        obj_mspec=obj_mspec,
                                        obj_permission=obj_permission,
                                        obj_roles=obj_roles,
                                        search_sub=1,
                                        REQUEST=REQUEST,
                                        apply_func=self.catalog_object,
                                        apply_path=path)

        elapse = time.time() - elapse
        c_elapse = time.clock() - c_elapse
        
        RESPONSE.redirect(URL1 + '/manage_catalogView?manage_tabs_message=' +
                          urllib.quote('Catalog Updated<br>Total time: %s<br>Total CPU time: %s' % (`elapse`, `c_elapse`)))


    def manage_addColumn(self, name, REQUEST=None, RESPONSE=None, URL1=None):
        """ add a column """
        self._catalog.addColumn(name)

        if REQUEST and RESPONSE:
            RESPONSE.redirect(URL1 + '/manage_catalogSchema?manage_tabs_message=Column%20Added')

    def manage_delColumns(self, names, REQUEST=None, RESPONSE=None, URL1=None):
        """ del a column """
        for name in names:
            self._catalog.delColumn(name)

        if REQUEST and RESPONSE:
            RESPONSE.redirect(URL1 + '/manage_catalogSchema?manage_tabs_message=Column%20Deleted')

    def manage_addIndex(self, name, type, REQUEST=None, RESPONSE=None, URL1=None):
        """ add an index """
        self._catalog.addIndex(name, type)
        
        if REQUEST and RESPONSE:
            RESPONSE.redirect(URL1 + '/manage_catalogIndexes?manage_tabs_message=Index%20Added')
        
    def manage_delIndexes(self, names, REQUEST=None, RESPONSE=None, URL1=None):
        """ del an index """
        for name in names:
            self._catalog.delIndex(name)
        
        if REQUEST and RESPONSE:
            RESPONSE.redirect(URL1 + '/manage_catalogIndexes?manage_tabs_message=Index%20Deleted')

    
    def catalog_object(self, obj, uid):
        """ wrapper around catalog """
        self._v_total = (self._v_total +
                         self._catalog.catalogObject(obj, uid, self.threshold))

        if self.threshold is not None:
            if self._v_total > self.threshold:
                # commit a subtransaction
                get_transaction().commit(1)
                # kick the chache, this may be overkill but ya never know
                self._p_jar.cacheFullSweep(1)
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
        return self.resolve_url(self.getpath(rid), REQUEST)

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
                          type(()): orify,
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

    def ZopeFindAndApply(self, obj, obj_ids=None, obj_metatypes=None,
                         obj_searchterm=None, obj_expr=None,
                         obj_mtime=None, obj_mspec=None,
                         obj_permission=None, obj_roles=None,
                         search_sub=0,
                         REQUEST=None, result=None, pre='',
                         apply_func=None, apply_path=''):
        """Zope Find interface and apply

        This is a *great* hack.  Zope find just doesn't do what we
        need here; the ability to apply a method to all the objects
        *as they're found* and the need to pass the object's path into 
        that method.

        """

        if result is None:
            result=[]

            if obj_metatypes and 'all' in obj_metatypes:
                obj_metatypes=None
                
            if obj_mtime and type(obj_mtime)==type('s'):
                obj_mtime=DateTime(obj_mtime).timeTime()

            if obj_permission:
                obj_permission=p_name(obj_permission)

            if obj_roles and type(obj_roles) is type('s'):
                obj_roles=[obj_roles]
                
            if obj_expr:
                # Setup expr machinations
                md=td()
                obj_expr=(Eval(obj_expr, expr_globals), md, md._push, md._pop)

        base=obj
        if hasattr(obj, 'aq_base'):
            base=obj.aq_base

        if not hasattr(base, 'objectItems'):
            return result
        try:    items=obj.objectItems()
        except: return result

        try: add_result=result.append
        except:
            raise AttributeError, `result`

        for id, ob in items:
            if pre: p="%s/%s" % (pre, id)
            else:   p=id
            
            dflag=0
            if hasattr(ob, '_p_changed') and (ob._p_changed == None):
                dflag=1

            if hasattr(ob, 'aq_base'):
                bs=ob.aq_base
            else: bs=ob

            if (
                (not obj_ids or absattr(bs.id) in obj_ids)
                and
                (not obj_metatypes or (hasattr(bs, 'meta_type') and
                 bs.meta_type in obj_metatypes))
                and
                (not obj_searchterm or
                 (hasattr(ob, 'PrincipiaSearchSource') and
                  string.find(ob.PrincipiaSearchSource(), obj_searchterm) >= 0
                  ))
                and
                (not obj_expr or expr_match(ob, obj_expr))
                and
                (not obj_mtime or mtime_match(ob, obj_mtime, obj_mspec))
                and
                ( (not obj_permission or not obj_roles) or \
                   role_match(ob, obj_permission, obj_roles)
                )
                ):
                if apply_func:
                    apply_func(ob, (apply_path+'/'+p))
                else:
                    add_result((p, ob))
                    dflag=0
                    
            if search_sub and hasattr(bs, 'objectItems'):
                self.ZopeFindAndApply(ob, obj_ids, obj_metatypes,
                                      obj_searchterm, obj_expr,
                                      obj_mtime, obj_mspec,
                                      obj_permission, obj_roles,
                                      search_sub,
                                      REQUEST, result, p,
                                      apply_func, apply_path)
            if dflag: ob._p_deactivate()

        return result



    def resolve_url(self, path, REQUEST):
        """ 
        Attempt to resolve a url into an object in the Zope
        namespace. The url may be absolute or a catalog path
        style url. If no object is found, None is returned.
        No exceptions are raised.
        """
        script=REQUEST.script
        if string.find(path, script) != 0:
            path='%s/%s' % (script, path) 
        try:    return REQUEST.resolve_url(path)
        except: return None


Globals.default__class_init__(ZCatalog)


def p_name(name):
    return '_' + string.translate(name, name_trans) + '_Permission'

def absattr(attr):
    if callable(attr): return attr()
    return attr


class td(TemplateDict):

    def validate(self, inst, parent, name, value, md):
        return getSecurityManager().validate(inst, parent, name, value)

def expr_match(ob, ed, c=InstanceDict, r=0):
    e, md, push, pop=ed
    push(c(ob, md))
    try: r=e.eval(md)
    finally:
        pop()
        return r

def mtime_match(ob, t, q, fn=hasattr):
    if not fn(ob, '_p_mtime'):
        return 0    
    return q=='<' and (ob._p_mtime < t) or (ob._p_mtime > t)

def role_match(ob, permission, roles, lt=type([]), tt=type(())):
    pr=[]
    fn=pr.append
    
    while 1:
        if hasattr(ob, permission):
            p=getattr(ob, permission)
            if type(p) is lt:
                map(fn, p)
                if hasattr(ob, 'aq_parent'):
                    ob=ob.aq_parent
                    continue
                break
            if type(p) is tt:
                map(fn, p)
                break
            if p is None:
                map(fn, ('Manager', 'Anonymous'))
                break

        if hasattr(ob, 'aq_parent'):
            ob=ob.aq_parent
            continue
        break

    for role in roles:
        if not (role in pr):
            return 0
    return 1



