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
__doc__="""Object Manager

$Id: ObjectManager.py,v 1.91 2000/05/16 19:34:43 brian Exp $"""

__version__='$Revision: 1.91 $'[11:-2]

import App.Management, Acquisition, Globals, CopySupport, Products
import os, App.FactoryDispatcher, ts_regex, Products
from Globals import HTMLFile, HTMLFile, Persistent
from Globals import MessageDialog, default__class_init__
from webdav.NullResource import NullResource
from webdav.Collection import Collection
from urllib import quote
from cStringIO import StringIO
import marshal
import App.Common
from AccessControl import getSecurityManager
from zLOG import LOG, ERROR
import sys

bad_id=ts_regex.compile('[^a-zA-Z0-9-_~\,\. ]').search #TS

class BeforeDeleteException( Exception ): pass # raise to veto deletion

_marker=[]
class ObjectManager(
    CopySupport.CopyContainer,
    App.Management.Navigation,
    App.Management.Tabs,
    Acquisition.Implicit,
    Persistent,
    Collection,
    ):
    """Generic object manager

    This class provides core behavior for collections of heterogeneous objects. 
    """

    __ac_permissions__=(
        ('View management screens', ('manage_main','manage_menu')),
        ('Access contents information',
         ('objectIds', 'objectValues', 'objectItems',''),
         ('Anonymous', 'Manager'),
         ),
        ('Delete objects',     ('manage_delObjects',)),
        ('FTP access',         ('manage_FTPstat','manage_FTPlist')),
        ('Import/Export objects',
         ('manage_importObject','manage_importExportForm',
          'manage_exportObject')
         ),
    )


    meta_type  ='Object Manager'

    meta_types=() # Sub-object types that are specific to this object
    
    _objects   =()

    manage_main=HTMLFile('main', globals())

    manage_options=(
        {'label':'Contents', 'action':'manage_main',
         'help':('OFSP','ObjectManager_Contents.dtml')},
        {'label':'Import/Export', 'action':'manage_importExportForm',
         'help':('OFSP','ObjectManager_Import-Export.dtml')},         
        )

    isAnObjectManager=1

    isPrincipiaFolderish=1

    def __class_init__(self):
        try:    mt=list(self.meta_types)
        except: mt=[]
        for b in self.__bases__:
            try:
                for t in b.meta_types:
                    if t not in mt: mt.append(t)
            except: pass
        mt.sort()
        self.meta_types=tuple(mt)
        
        default__class_init__(self)

    def all_meta_types(self):
        pmt=()
        if hasattr(self, '_product_meta_types'): pmt=self._product_meta_types
        elif hasattr(self, 'aq_acquire'):
            try: pmt=self.aq_acquire('_product_meta_types')
            except:  pass
        return self.meta_types+Products.meta_types+pmt

    def _subobject_permissions(self):
        return (Products.__ac_permissions__+
                self.aq_acquire('_getProductRegistryData')('ac_permissions')
                )


    def filtered_meta_types(self, user=None):
        "Those meta types for which a user has adequite permissions."

        user=getSecurityManager().getUser()
        
        meta_types=[]
        if callable(self.all_meta_types):
            all=self.all_meta_types()
        else:
            all=self.all_meta_types

        for meta_type in all:
            if meta_type.has_key('permission'):
                if user.has_permission(meta_type['permission'],self):
                    meta_types.append(meta_type)
            else:
                meta_types.append(meta_type)
        return meta_types

    def _checkId(self, id, allow_dup=0):
        # If allow_dup is false, an error will be raised if an object
        # with the given id already exists. If allow_dup is true,
        # only check that the id string contains no illegal chars.
        if not id or (type(id) != type('')):
            raise 'Bad Request', 'Empty or invalid specified'
        if bad_id(id) != -1:
            raise 'Bad Request', (
            'The id %s contains characters illegal in URLs.' % id)
        if id[0]=='_': raise 'Bad Request', (
            'The id %s  is invalid - it begins with an underscore.'  % id)
        if not allow_dup:
            if hasattr(self, 'aq_base'):
                self=self.aq_base
            if hasattr(self, id):
                raise 'Bad Request', (
                    'The id %s is invalid - it is already in use.' % id)
        if id == 'REQUEST':
            raise 'Bad Request', 'REQUEST is a reserved name.'
        if '/' in id:
            raise 'Bad Request', (
                'The id %s contains characters illegal in URLs.' % id
                )

    def _setOb(self, id, object): setattr(self, id, object)
    def _delOb(self, id): delattr(self, id)
    def _getOb(self, id, default=_marker):
        if hasattr(self, 'aq_base'):
            base=self.aq_base
        else: base=self
        if not hasattr(base, id):
            if default is _marker:
                raise AttributeError, id
            return default
        return getattr(self, id)

    def _setObject(self,id,object,roles=None,user=None):
        v=self._checkId(id)
        if v is not None: id=v
        try:    t=object.meta_type
        except: t=None
        self._objects=self._objects+({'id':id,'meta_type':t},)
        self._setOb(id,object)
        object=self._getOb(id)
        object.manage_fixupOwnershipAfterAdd()
        object.manage_afterAdd(object, self)
        
        # Try to give user the local role "Owner", but only if
        # no local roles have been set on the object yet.
        if hasattr(object, '__ac_local_roles__'):
            if object.__ac_local_roles__ is None:
                user=getSecurityManager().getUser()
                name=user.getUserName()
                if name != 'Anonymous User':
                    object.manage_setLocalRoles(name, ['Owner'])
        return id

    def manage_afterAdd(self, item, container):
        for object in self.objectValues():
            try: s=object._p_changed
            except: s=0
            object.manage_afterAdd(item, container)
            if s is None: object._p_deactivate()

    def manage_afterClone(self, item):
        for object in self.objectValues():
            try: s=object._p_changed
            except: s=0
            object.manage_afterClone(item)
            if s is None: object._p_deactivate()

    def manage_beforeDelete(self, item, container):
        for object in self.objectValues():
            try: s=object._p_changed
            except: s=0
            try:
                 object.manage_beforeDelete(item, container)
            except BeforeDeleteException, ob:
                raise
            except:
                LOG('Zope',ERROR,'manage_beforeDelete() threw',
                    error=sys.exc_info())
                pass
            if s is None: object._p_deactivate()

    def _delObject(self, id, dp=1):
        object=self._getOb(id)
        try:
            object.manage_beforeDelete(object, self)
        except BeforeDeleteException, ob:
            raise
        except:
            LOG('Zope',ERROR,'manage_beforeDelete() threw',
                error=sys.exc_info())
            pass
        self._objects=tuple(filter(lambda i,n=id: i['id']!=n, self._objects))
        self._delOb(id)

    def objectIds(self, spec=None):
        """Return a list of subobject ids.

        Returns a list of subobject ids of the current object.  If 'spec' is
        specified, returns objects whose meta_type matches 'spec'.
        """
        if spec is not None:
            if type(spec)==type('s'):
                spec=[spec]
            set=[]
            for ob in self._objects:
                if ob['meta_type'] in spec:
                    set.append(ob['id'])
            return set
        return map(lambda i: i['id'], self._objects)

    def objectValues(self, spec=None):
        """Return a list of the actual subobjects.

        Returns a list of actual subobjects of the current object.  If
        'spec' is specified, returns only objects whose meta_type match 'spec'
        """
        return map(self._getOb, self.objectIds(spec))

    def objectItems(self, spec=None):
        """Return a list of (id, subobject) tuples.

        Returns a list of (id, subobject) tuples of the current object.
        If 'spec' is specified, returns only objects whose meta_type match
        'spec'
        """
        r=[]
        a=r.append
        g=self._getOb
        for id in self.objectIds(spec): a((id, g(id)))
        return r

    def objectMap(self):
        # Return a tuple of mappings containing subobject meta-data
        return self._objects

    def objectIds_d(self,t=None):
        if hasattr(self, '_reserved_names'): n=self._reserved_names
        else: n=()
        if not n: return self.objectIds(t)
        r=[]
        a=r.append
        for id in self.objectIds(t):
            if id not in n: a(id)
        return r

    def objectValues_d(self,t=None):
        return map(self._getOb, self.objectIds_d(t))

    def objectItems_d(self,t=None):
        r=[]
        a=r.append
        g=self._getOb
        for id in self.objectIds_d(t): a((id, g(id)))
        return r

    def objectMap_d(self,t=None):
        if hasattr(self, '_reserved_names'): n=self._reserved_names
        else: n=()
        if not n: return self._objects
        r=[]
        a=r.append
        for d in self._objects:
            if d['id'] not in n: a(d)
        return r

    def superValues(self,t):
        """Return all of the objects of a given type

        The search is performed in this folder and in folders above.
        """
        if type(t)==type('s'): t=(t,)
        obj=self
        seen={}
        vals=[]
        have=seen.has_key
        x=0
        while x < 100:
            if not hasattr(obj,'_getOb'): break
            get=obj._getOb
            if hasattr(obj,'_objects'):
                for i in obj._objects:
                    try:
                        id=i['id']
                        if (not have(id)) and (i['meta_type'] in t):
                            vals.append(get(id))
                            seen[id]=1
                    except: pass
                    
            if hasattr(obj,'aq_parent'): obj=obj.aq_parent
            else:                        return vals
            x=x+1
        return vals


    manage_addProduct=App.FactoryDispatcher.ProductDispatcher()

    def manage_delObjects(self, ids=[], REQUEST=None):
        """Delete a subordinate object
        
        The objects specified in 'ids' get deleted.
        """
        if type(ids) is type(''): ids=[ids]
        if not ids:
            return MessageDialog(title='No items specified',
                   message='No items were specified!',
                   action ='./manage_main',)
        try:    p=self._reserved_names
        except: p=()
        for n in ids:
            if n in p:
                return MessageDialog(title='Not Deletable',
                       message='<EM>%s</EM> cannot be deleted.' % n,
                       action ='./manage_main',)
        while ids:
            id=ids[-1]
            v=self._getOb(id, self)
            if v is self:
                raise 'BadRequest', '%s does not exist' % ids[-1]
            self._delObject(id)
            del ids[-1]
        if REQUEST is not None:
                return self.manage_main(self, REQUEST, update_menu=1)


    def tpValues(self):
        """Returns a list of the folder's sub-folders, used by tree tag."""
        r=[]
        if hasattr(self.aq_base,'tree_ids'):
            for id in self.aq_base.tree_ids:
                if hasattr(self, id): r.append(self._getOb(id))
        else:
            for id in self._objects:
                o=self._getOb(id['id'])
                try:
                    if o.isPrincipiaFolderish: r.append(o)
                except: pass

        return r

    # The Following methods are short-term measures to get Paul off my back;)
    def manage_exportHack(self, id=None):
        """Exports a folder and its contents to /var/export.bbe
        This file can later be imported by using manage_importHack"""
        if id is None: o=self
        else: o=self._getOb(id)
        f=Globals.data_dir+'/export.bbe'
        o._p_jar.exportFile(o._p_oid,f)
        return f

    def manage_importHack(self, REQUEST=None):
        "Imports a previously exported object from /var/export.bbe"
        f=Globals.data_dir+'/export.bbe'
        o=self._p_jar.importFile(f)
        id=o.id
        if hasattr(id,'im_func'): id=id()
        self._setObject(id,o)
        return 'OK, I imported %s' % id

    # These methods replace manage_importHack and manage_exportHack

    def manage_exportObject(self, id='', download=None, toxml=None,
                            RESPONSE=None):
        """Exports an object to a file and returns that file."""        
        if not id:
            id=self.id
            if callable(id): id=id()
            ob=self
        else: ob=self._getOb(id)

        suffix=toxml and 'xml' or 'zexp'
        
        if download:
            f=StringIO()
            if toxml: ob._p_jar.exportXML(ob._p_oid, f)
            else:     ob._p_jar.exportFile(ob._p_oid, f)
            RESPONSE.setHeader('Content-type','application/data')
            RESPONSE.setHeader('Content-Disposition',
                'inline;filename=%s.%s' % (id, suffix))
            return f.getvalue()

        f=Globals.data_dir+'/%s.%s' % (id, suffix)
        if toxml: ob._p_jar.exportXML(ob._p_oid, f)
        else:     ob._p_jar.exportFile(ob._p_oid, f)

        if RESPONSE is not None:
            return MessageDialog(
                    title="Object exported",
                    message="<EM>%s</EM> sucessfully\
                    exported to <pre>%s</pre>." % (id, f),
                    action="manage_main")

    manage_importExportForm=HTMLFile('importExport',globals())

    def manage_importObject(self, file, REQUEST=None):
        """Import an object from a file"""
        dirname, file=os.path.split(file)
        if dirname:
            raise 'Bad Request', 'Invalid file name %s' % file
        file=os.path.join(INSTANCE_HOME, 'import', file)
        if not os.path.exists(file):
            raise 'Bad Request', 'File does not exist: %s' % file
        # locate a valid connection
        connection=self._p_jar
        obj=self
        while connection is None:
            obj=obj.aq_parent
            connection=obj._p_jar
        ob=connection.importFile(file)
        if REQUEST: self._verifyObjectPaste(ob, REQUEST)
        id=ob.id
        if hasattr(id, 'im_func'): id=id()
        self._setObject(id, ob)
        if REQUEST is not None:
            return MessageDialog(
                title='Object imported',
                message='<EM>%s</EM> sucessfully imported' % id,
                action='manage_main'
                )

    # FTP support methods
    
    def manage_FTPlist(self,REQUEST):
        "Directory listing for FTP"
        out=()
        
        # check to see if we are being acquiring or not
        ob=self
        while 1:
            if App.Common.is_acquired(ob):
                raise ValueError('FTP List not supported on acquired objects')
            if not hasattr(ob,'aq_parent'):
                break
            ob=ob.aq_parent
        
        files=self.objectItems()
        try:
            files.sort()
        except AttributeError:
            files=list(files)
            files.sort()
            
        if not (hasattr(self,'isTopLevelPrincipiaApplicationObject') and
                self.isTopLevelPrincipiaApplicationObject):
            files.insert(0,('..',self.aq_parent))
        for k,v in files:
            stat=marshal.loads(v.manage_FTPstat(REQUEST))
            out=out+((k,stat),)
        return marshal.dumps(out)   

    def manage_FTPstat(self,REQUEST):
        "Psuedo stat used for FTP listings"
        mode=0040000
        from AccessControl.User import nobody
        # check to see if we are acquiring our objectValues or not
        if not (len(REQUEST.PARENTS) > 1 and
                self.objectValues() == REQUEST.PARENTS[1].objectValues()):
            try:
                if getSecurityManager().validateValue(self.manage_FTPlist):
                    mode=mode | 0770
            except: pass
            if nobody.allowed(
                        self.manage_FTPlist,
                        self.manage_FTPlist.__roles__):
                mode=mode | 0007
        mtime=self.bobobase_modification_time().timeTime()
        # get owner and group
        owner=group='Zope'
        for user, roles in self.get_local_roles():
            if 'Owner' in roles:
                owner=user
                break
        return marshal.dumps((mode,0,0,1,owner,group,0,mtime,mtime,mtime))


    def __getitem__(self, key):
        v=self._getOb(key, None)
        if v is not None: return v
        if hasattr(self, 'REQUEST'):
            request=self.REQUEST
            method=request.get('REQUEST_METHOD', 'GET')
            if not method in ('GET', 'POST'):
                return NullResource(self, key, request).__of__(self)
        raise KeyError, key


Globals.default__class_init__(ObjectManager)

class PUTer(Acquisition.Explicit):
    """Class to support the HTTP PUT protocol."""

    def __init__(self, parent, id):
        self.id=id
        self.__parent__=parent
        self.__roles__ =parent.PUT__roles__
        
    def PUT(self, REQUEST, RESPONSE):
        """Adds a document, image or file to the folder when a PUT
        request is received."""
        name=self.id
        type=REQUEST.get_header('content-type', None)
        body=REQUEST.get('BODY', '')
        if type is None:
            type, enc=mimetypes.guess_type(name)
        if type is None:
            if content_types.find_binary(body) >= 0:
                type='application/octet-stream'
            else: type=content_types.text_type(body)
        type=lower(type)
        if type in ('text/html', 'text/xml', 'text/plain'):
            self.__parent__.manage_addDTMLDocument(name, '', body)
        elif type[:6]=='image/':
            ob=Image(name, '', body, content_type=type)
            self.__parent__._setObject(name, ob)
        else:
            ob=File(name, '', body, content_type=type)
            self.__parent__._setObject(name, ob)
        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE

    def __str__(self):
        return self.id
