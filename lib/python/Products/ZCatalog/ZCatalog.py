##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""ZCatalog product"""

from Globals import DTMLFile, MessageDialog
import Globals

from OFS.Folder import Folder
from OFS.FindSupport import FindSupport
from OFS.ObjectManager import ObjectManager
from DateTime import DateTime
from Acquisition import Implicit
from Persistence import Persistent
from DocumentTemplate.DT_Util import InstanceDict, TemplateDict
from DocumentTemplate.DT_Util import Eval
from AccessControl.Permission import name_trans
from Catalog import Catalog, CatalogError
from AccessControl import getSecurityManager
from AccessControl.DTML import RestrictedDTML
from zLOG import LOG, ERROR
from ZCatalogIndexes import ZCatalogIndexes
from Products.PluginIndexes.common.PluggableIndex \
     import PluggableIndexInterface
from Products.PluginIndexes.TextIndex.Vocabulary import Vocabulary
from Products.PluginIndexes.TextIndex import Splitter
import urllib, os, sys, time, types
import string
from IZCatalog import IZCatalog


manage_addZCatalogForm=DTMLFile('dtml/addZCatalog',globals())

def manage_addZCatalog(self, id, title,
                       vocab_id=None, # Deprecated
                       REQUEST=None):
    """Add a ZCatalog object
    """
    id=str(id)
    title=str(title)        
    c=ZCatalog(id, title, vocab_id, self)
    self._setObject(id, c)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST,update_menu=1)


class ZCatalog(Folder, Persistent, Implicit):
    __implements__ = IZCatalog

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

    manage_options = (
        {'label': 'Contents',           # TAB: Contents
         'action': 'manage_main',
         'help': ('OFSP','ObjectManager_Contents.stx')},
        {'label': 'Catalog',            # TAB: Cataloged Objects
         'action': 'manage_catalogView',
         'help':('ZCatalog','ZCatalog_Cataloged-Objects.stx')},
        {'label': 'Properties',         # TAB: Properties
         'action': 'manage_propertiesForm',
         'help': ('OFSP','Properties.stx')},
        {'label': 'Indexes',            # TAB: Indexes
         'action': 'manage_catalogIndexes',
         'help': ('ZCatalog','ZCatalog_Indexes.stx')},
        {'label': 'Metadata',           # TAB: Metadata
         'action': 'manage_catalogSchema', 
         'help':('ZCatalog','ZCatalog_MetaData-Table.stx')},
        {'label': 'Find Objects',       # TAB: Find Objects
         'action': 'manage_catalogFind', 
         'help':('ZCatalog','ZCatalog_Find-Items-to-ZCatalog.stx')},
        {'label': 'Advanced',           # TAB: Advanced
         'action': 'manage_catalogAdvanced', 
         'help':('ZCatalog','ZCatalog_Advanced.stx')},
        {'label': 'Undo',               # TAB: Undo
         'action': 'manage_UndoForm',
         'help': ('OFSP','Undo.stx')},
        {'label': 'Security',           # TAB: Security
         'action': 'manage_access',
         'help': ('OFSP','Security.stx')},
        {'label': 'Ownership',          # TAB: Ownership
         'action': 'manage_owner',
         'help': ('OFSP','Ownership.stx'),}
        )

    __ac_permissions__=(

        ('Manage ZCatalog Entries',
         ['manage_catalogObject', 'manage_uncatalogObject',
          'catalog_object', 'uncatalog_object', 'refreshCatalog',
          
          'manage_catalogView', 'manage_catalogFind',
          'manage_catalogSchema', 'manage_catalogIndexes',
          'manage_catalogAdvanced', 'manage_objectInformation',
          
          'manage_catalogReindex', 'manage_catalogFoundItems',
          'manage_catalogClear', 'manage_addColumn', 'manage_delColumn',
          'manage_addIndex', 'manage_delIndex', 'manage_clearIndex',
          'manage_reindexIndex', 'manage_main', 'availableSplitters',
          
          # these two are deprecated:
          'manage_delColumns', 'manage_deleteIndex'
          ], 
         ['Manager']),

        ('Search ZCatalog',
         ['searchResults', '__call__', 'uniqueValuesFor',
          'getpath', 'schema', 'indexes', 'index_objects', 'getIndexObjects'
          'all_meta_types', 'valid_roles', 'resolve_url',
          'getobject'],
         ['Anonymous', 'Manager']), 
        )


    manage_catalogAddRowForm = DTMLFile('dtml/catalogAddRowForm', globals())
    manage_catalogView = DTMLFile('dtml/catalogView',globals())
    manage_catalogFind = DTMLFile('dtml/catalogFind',globals())
    manage_catalogSchema = DTMLFile('dtml/catalogSchema', globals())
    manage_catalogIndexes = DTMLFile('dtml/catalogIndexes', globals())
    manage_catalogAdvanced = DTMLFile('dtml/catalogAdvanced', globals())
    manage_objectInformation = DTMLFile('dtml/catalogObjectInformation',
                                        globals())

    Indexes = ZCatalogIndexes()

    threshold=10000
    _v_total=0
    _v_transaction = None
    
    def __init__(self, id, title='', vocab_id=None, container=None):
        # ZCatalog no longer cares about vocabularies
        # so the vocab_id argument is ignored (Casey)
        
        if container is not None:
            self=self.__of__(container)
        self.id=id
        self.title=title
        
        # vocabulary and vocab_id are left for backwards 
        # compatibility only, they are not used anymore
        self.vocabulary = None
        self.vocab_id = ''        
        
        self.threshold = 10000
        self._v_total = 0

        self._catalog = Catalog()

    def __len__(self):
        return len(self._catalog)
    
    
    # getVocabulary method is no longer supported
    # def getVocabulary(self):
    #   """ more ack! """
    #   return getattr(self, self.vocab_id)


    def manage_edit(self, RESPONSE, URL1, threshold=1000, REQUEST=None):
        """ edit the catalog """
        if type(threshold) is not type(1):
            threshold=int(threshold)
        self.threshold = threshold

        RESPONSE.redirect(
            URL1 + '/manage_main?manage_tabs_message=Catalog%20Changed')


    def manage_subbingToggle(self, REQUEST, RESPONSE, URL1):
        """ toggle subtransactions """
        if self.threshold:
            self.threshold = None
        else:
            self.threshold = 10000
        
        RESPONSE.redirect(
            URL1 +
            '/manage_catalogAdvanced?manage_tabs_message=Catalog%20Changed')

    def manage_catalogObject(self, REQUEST, RESPONSE, URL1, urls=None):
        """ index Zope object(s) that 'urls' point to """
        if urls:
            if isinstance(urls, types.StringType):
                urls=(urls,)
                
            for url in urls:
                obj = self.resolve_path(url)
                if not obj:
                    obj = self.resolve_url(url, REQUEST)
                if obj is not None: 
                    self.catalog_object(obj, url)

        RESPONSE.redirect(
            URL1 +
            '/manage_catalogView?manage_tabs_message=Object%20Cataloged')


    def manage_uncatalogObject(self, REQUEST, RESPONSE, URL1, urls=None):
        """ removes Zope object(s) 'urls' from catalog """

        if urls:
            if isinstance(urls, types.StringType):
                urls=(urls,)

            for url in urls:
                self.uncatalog_object(url)

        RESPONSE.redirect(
            URL1 +
            '/manage_catalogView?manage_tabs_message=Object%20Uncataloged')


    def manage_catalogReindex(self, REQUEST, RESPONSE, URL1):
        """ clear the catalog, then re-index everything """

        elapse = time.time()
        c_elapse = time.clock()

        self.refreshCatalog(clear=1)

        elapse = time.time() - elapse
        c_elapse = time.clock() - c_elapse
        
        RESPONSE.redirect(
            URL1 +
            '/manage_catalogAdvanced?manage_tabs_message=' +
            urllib.quote('Catalog Updated<br>'
                         'Total time: %s<br>'
                         'Total CPU time: %s' % (`elapse`, `c_elapse`)))
        

    def refreshCatalog(self, clear=0):
        """ re-index everything we can find """

        cat = self._catalog
        paths = cat.paths.values()
        if clear:
            paths = tuple(paths)
            cat.clear()

        for p in paths:
            obj = self.resolve_path(p)
            if not obj:
                obj = self.resolve_url(p, self.REQUEST)
            if obj is not None:
                self.catalog_object(obj, p)

    def manage_catalogClear(self, REQUEST=None, RESPONSE=None, URL1=None):
        """ clears the whole enchilada """
        self._catalog.clear()

        if REQUEST and RESPONSE:
            RESPONSE.redirect(
              URL1 +
              '/manage_catalogAdvanced?manage_tabs_message=Catalog%20Cleared')


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
        obj = REQUEST.PARENTS[1]
        path = '/'.join(obj.getPhysicalPath())

        
        results = self.ZopeFindAndApply(obj,
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
        
        RESPONSE.redirect(
            URL1 +
            '/manage_catalogView?manage_tabs_message=' +
            urllib.quote(
            'Catalog Updated<br>Total time: %s<br>Total CPU time: %s' %
            (`elapse`, `c_elapse`)))


    def manage_addColumn(self, name, REQUEST=None, RESPONSE=None, URL1=None):
        """ add a column """
        self.addColumn(name)

        if REQUEST and RESPONSE:
            RESPONSE.redirect(
                URL1 +
                '/manage_catalogSchema?manage_tabs_message=Column%20Added')


    def manage_delColumns(self, names, REQUEST=None, RESPONSE=None, URL1=None):
        """ Deprecated method. Use manage_delColumn instead. """
        # log a deprecation warning
        import warnings
        warnings.warn(
            "The manage_delColumns method of ZCatalog is deprecated"
            "since Zope 2.4.2.\n"
            "This method is only kept for backwards compatibility "
            "for a while\n"
            "and will go away in a future release.\n"
            "\n"
            "Please use instead the manage_delColumn method.\n"
            ,DeprecationWarning)
        
        self.manage_delColumn(names, REQUEST=REQUEST, RESPONSE=RESPONSE,
                              URL1=URL1)


    def manage_delColumn(self, names, REQUEST=None, RESPONSE=None, URL1=None):
        """ delete a column or some columns """
        if isinstance(names, types.StringType):
            names = (names,)
            
        for name in names:
            self.delColumn(name)

        if REQUEST and RESPONSE:
            RESPONSE.redirect(
                URL1 +
                '/manage_catalogSchema?manage_tabs_message=Column%20Deleted')


    def manage_addIndex(self, name, type, extra=None,
                        REQUEST=None, RESPONSE=None, URL1=None):
        """add an index """
        self.addIndex(name, type,extra)

        if REQUEST and RESPONSE:
            RESPONSE.redirect(
                URL1 +
                '/manage_catalogIndexes?manage_tabs_message=Index%20Added')
        

    def manage_deleteIndex(self, ids=None, REQUEST=None, RESPONSE=None,
        URL1=None):
        """ Deprecated method. Use manage_delIndex instead. """
        # log a deprecation warning
        import warnings
        warnings.warn(
            "The manage_deleteIndex method of ZCatalog is deprecated"
            "since Zope 2.4.2.\n"
            "This method is only kept for backwards compatibility for a "
            "while\n"
            "and will go away in a future release.\n"
            "\n"
            "Please use instead the manage_delIndex method.\n"
            ,DeprecationWarning)
        
        self.manage_delIndex(ids=ids, REQUEST=REQUEST, RESPONSE=RESPONSE,
                             URL1=URL1)


    def manage_delIndex(self, ids=None, REQUEST=None, RESPONSE=None,
        URL1=None):
        """ delete an index or some indexes """
        if not ids:
            return MessageDialog(title='No items specified',
                message='No items were specified!',
                action = "./manage_catalogIndexes",)

        if isinstance(ids, types.StringType):
            ids = (ids,)

        for name in ids:
            self.delIndex(name)
        
        if REQUEST and RESPONSE:
            RESPONSE.redirect(
                URL1 +
                '/manage_catalogIndexes?manage_tabs_message=Index%20Deleted')


    def manage_clearIndex(self, ids=None, REQUEST=None, RESPONSE=None,
        URL1=None):
        """ clear an index or some indexes """
        if not ids:
            return MessageDialog(title='No items specified',
                message='No items were specified!',
                action = "./manage_catalogIndexes",)

        if isinstance(ids, types.StringType):
            ids = (ids,)

        for name in ids:
            self.clearIndex(name)
        
        if REQUEST and RESPONSE:
            RESPONSE.redirect(
                URL1 +
                '/manage_catalogIndexes?manage_tabs_message=Index%20Cleared')


    def reindexIndex(self,name,REQUEST):
        
        paths = tuple(self._catalog.paths.values())

        for p in paths:
            obj = self.resolve_path(p)
            if not obj:
                obj = self.resolve_url(p, REQUEST)
            if obj is not None:
                self.catalog_object(obj, p, idxs=[name])             


    def manage_reindexIndex(self, ids=None, REQUEST=None, RESPONSE=None,
                            URL1=None):
        """Reindex indexe(s) from a ZCatalog"""
        if not ids:
            return MessageDialog(title='No items specified',
                message='No items were specified!',
                action = "./manage_catalogIndexes",)
                
        if isinstance(ids, types.StringType):
            ids = (ids,)

        for name in ids:
            self.reindexIndex(name, REQUEST)

        if REQUEST and RESPONSE:
            RESPONSE.redirect(
                URL1 +
                '/manage_catalogIndexes'
                '?manage_tabs_message=Reindexing%20Performed')


    def availableSplitters(self):
        """ splitter we can add """
        return Splitter.availableSplitters


    def catalog_object(self, obj, uid=None, idxs=[]):
        """ wrapper around catalog """

        if uid is None:
            try: uid = obj.getPhysicalPath
            except AttributeError:
                raise CatalogError(
                    "A cataloged object must support the 'getPhysicalPath' "
                    "method if no unique id is provided when cataloging"
                    )
            else: uid='/'.join(uid())
        elif not isinstance(uid,types.StringType):
            raise CatalogError('The object unique id must be a string.')

        self._catalog.catalogObject(obj, uid, None,idxs)
        # None passed in to catalogObject as third argument indicates
        # that we shouldn't try to commit subtransactions within any
        # indexing code.  We throw away the result of the call to
        # catalogObject (which is a word count), because it's
        # worthless to us here.
        
        if self.threshold is not None:
            # figure out whether or not to commit a subtransaction.
            t = id(get_transaction())
            if t != self._v_transaction:
                self._v_total = 0
            self._v_transaction = t
            self._v_total = self._v_total + 1
            # increment the _v_total counter for this thread only and get
            # a reference to the current transaction.
            # the _v_total counter is zeroed if we notice that we're in
            # a different transaction than the last one that came by.
            # self.threshold represents the number of times that
            # catalog_object needs to be called in order for the catalog
            # to commit a subtransaction.  The semantics here mean that
            # we should commit a subtransaction if our threshhold is
            # exceeded within the boundaries of the current transaction.
            if self._v_total > self.threshold:
                get_transaction().commit(1)
                self._p_jar.cacheGC()
                self._v_total = 0

    def uncatalog_object(self, uid):
        """Wrapper around catalog """
        self._catalog.uncatalogObject(uid)

    def uniqueValuesFor(self, name):
        """Return the unique values for a given FieldIndex """
        return self._catalog.uniqueValuesFor(name)

    def getpath(self, rid):
        """Return the path to a cataloged object given a 'data_record_id_'
        """
        return self._catalog.paths[rid]

    def getrid(self, path, default=None):
        """Return 'data_record_id_' the to a cataloged object given a 'path'
        """
        return self._catalog.uids.get(path, default)

    def getobject(self, rid, REQUEST=None):
        """Return a cataloged object given a 'data_record_id_'
        """
        obj = self.aq_parent.unrestrictedTraverse(self.getpath(rid))
        if not obj:
            if REQUEST is None:
                REQUEST=self.REQUEST
            obj = self.resolve_url(self.getpath(rid), REQUEST)
        return obj

    def getMetadataForRID(self, rid):
        """return the correct metadata for the cataloged record id"""
        return self._catalog.getMetadataForRID(int(rid))

    def getIndexDataForRID(self, rid):
        """return the current index contents for the specific rid"""
        return self._catalog.getIndexDataForRID(rid)
    
    def schema(self):
        return self._catalog.schema.keys()

    def indexes(self):
        return self._catalog.indexes.keys()

    def index_objects(self):
        # This method returns unwrapped indexes!
        # You should probably use getIndexObjects instead
        return self._catalog.indexes.values()
        
    def getIndexObjects(self):
        # Return a list of wrapped(!) indexes
        catalog = self._catalog
        return [index.__of__(catalog) for index in catalog.indexes.values()]

    def _searchable_arguments(self):
        r = {}
        n={'optional':1}
        for name in self._catalog.indexes.keys():
            r[name]=n
        return r

    def _searchable_result_columns(self):
        r = []
        for name in self._catalog.schema.keys():
            i = {}
            i['name'] = name
            i['type'] = 's'
            i['parser'] = str
            i['width'] = 8
            r.append(i)
        r.append({'name': 'data_record_id_',
                  'type': 's',
                  'parser': str,
                  'width': 8})
        return r

    def searchResults(self, REQUEST=None, used=None, **kw):
        """Search the catalog according to the ZTables search interface.
        
        Search terms can be passed in the REQUEST or as keyword
        arguments. 
        """

        return self._catalog.searchResults(REQUEST, used, **kw)

    __call__=searchResults

## this stuff is so the find machinery works

    meta_types=() # Sub-object types that are specific to this object
    
    # Dont need this anymore -- we inherit from object manager
    #def all_meta_types(self):
    #    pmt=()
    #    if hasattr(self, '_product_meta_types'): pmt=self._product_meta_types
    #    elif hasattr(self, 'aq_acquire'):
    #        try: pmt=self.aq_acquire('_product_meta_types')
    #        except AttributeError:  pass
    #    return self.meta_types+Products.meta_types+pmt

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
                obj_expr=(Eval(obj_expr), md, md._push, md._pop)

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
                  ob.PrincipiaSearchSource().find(obj_searchterm) >= 0
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
        if path.find(script) != 0:
            path='%s/%s' % (script, path) 
        try: return REQUEST.resolve_url(path)
        except: pass

    def resolve_path(self, path):
        """ 
        Attempt to resolve a url into an object in the Zope
        namespace. The url may be absolute or a catalog path
        style url. If no object is found, None is returned.
        No exceptions are raised.
        """
        try: return self.unrestrictedTraverse(path)
        except: pass

    def manage_normalize_paths(self, REQUEST):
        """Ensure that all catalog paths are full physical paths

        This should only be used with ZCatalogs in which all paths can
        be resolved with unrestrictedTraverse."""

        paths = self._catalog.paths
        uids = self._catalog.uids
        unchanged = 0
        fixed = []
        removed = []

        for path, rid in uids.items():
            ob = None
            if path[:1] == '/':
                ob = self.resolve_url(path[1:],REQUEST)
            if ob is None:
                ob = self.resolve_url(path, REQUEST)
                if ob is None:
                    removed.append(path)
                    continue
            ppath = '/'.join(ob.getPhysicalPath())
            if path != ppath:
                fixed.append((path, ppath))
            else:
                unchanged = unchanged + 1

        for path, ppath in fixed:
            rid = uids[path]
            del uids[path]
            paths[rid] = ppath
            uids[ppath] = rid
        for path in removed:
            self.uncatalog_object(path)

        return MessageDialog(title='Done Normalizing Paths',
          message='%s paths normalized, %s paths removed, and '
                  '%s unchanged.' % (len(fixed), len(removed), unchanged),
          action='./manage_main')

    def manage_convertBTrees(self, threshold=200):
        """Convert the catalog's data structures to use BTrees package"""
        assert type(threshold) is type(0)
        tt=time.time()
        ct=time.clock()
        self._catalog._convertBTrees(threshold)
        tt=time.time()-tt
        ct=time.clock()-ct
        return 'Finished conversion in %s seconds (%s cpu)' % (tt, ct)


    def manage_convertIndex(self, ids, REQUEST=None, RESPONSE=None, URL1=None):
        """convert old-style indexes to new-style indexes"""

        from Products.PluginIndexes.KeywordIndex import KeywordIndex 
        from Products.PluginIndexes.FieldIndex import FieldIndex
        from Products.PluginIndexes.TextIndex import TextIndex

        converted = []
        for id in ids:
            idx = self.Indexes[id]

            iface = getattr(idx,'__implements__',None)
            if iface is None:

                mt = idx.meta_type

                converted.append(id)
                self.delIndex(id)

                if mt in ('Field Index','Keyword Index'):
                    self.addIndex(id,mt.replace(' ',''))
                elif mt == 'Text Index':
                    # TODO: Lexicon handling to be added
                    self.addIndex(id,'TextIndex')

        if converted:
            RESPONSE.redirect(
                URL1 +
                '/manage_main?manage_tabs_message=Indexes%20converted')
        else:
            RESPONSE.redirect(
                URL1 +
                '/manage_main?'
                'manage_tabs_message='
                'No%20indexes%20found%20to%20be%20converted')
                    

    #
    # Indexing methods 
    #

    def addIndex(self, name, type,extra=None):
        # Convert the type by finding an appropriate product which supports
        # this interface by that name.  Bleah

        products = ObjectManager.all_meta_types(self, interfaces=(
            PluggableIndexInterface,))

        p = None

        for prod in products:
            if prod['name'] == type: 
                p = prod
                break

        if p is None:
            raise ValueError, "Index of type %s not found" % type

        base = p['instance']

        if base is None:
            raise ValueError, "Index type %s does not support addIndex" % type

        # This code is somewhat lame but every index type has its own
        # function signature *sigh* and there is no common way to pass
        # additional parameters to the constructor. The suggested way
        # for new index types is to use an "extra" record.

        if 'extra' in base.__init__.func_code.co_varnames:
            index = apply(base,(name,), {"extra":extra,"caller":self})
        else:
            index = base(name,self)
        
        self._catalog.addIndex(name,index)


    def delIndex(self, name ):
        self._catalog.delIndex(name)

    def clearIndex(self, name):
        self._catalog.getIndex(name).clear()


    def addColumn(self, name, default_value=None):
        return self._catalog.addColumn(name, default_value)

    def delColumn(self, name):
        return self._catalog.delColumn(name)

    
Globals.default__class_init__(ZCatalog)


def p_name(name):
    return '_' + string.translate(name, name_trans) + '_Permission'

def absattr(attr):
    if callable(attr): return attr()
    return attr


class td(RestrictedDTML, TemplateDict):
    pass

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
