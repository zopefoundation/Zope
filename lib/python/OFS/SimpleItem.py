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
'''This module implements a simple item mix-in for objects that have a
very simple (e.g. one-screen) management interface, like documents,
Aqueduct database adapters, etc.

This module can also be used as a simple template for implementing new
item types. 

$Id: SimpleItem.py,v 1.75 2000/06/01 17:29:37 jim Exp $'''
__version__='$Revision: 1.75 $'[11:-2]

import regex, sys, Globals, App.Management, Acquisition, App.Undo
import AccessControl.Role, AccessControl.Owned, App.Common
from webdav.Resource import Resource
from ExtensionClass import Base
from DateTime import DateTime
from CopySupport import CopySource
from string import join, lower, find, split
from types import InstanceType, StringType
from ComputedAttribute import ComputedAttribute
from urllib import quote, unquote
from AccessControl import getSecurityManager

import marshal
import ZDOM

HTML=Globals.HTML
_marker=[]
StringType=type('')

class Item(Base, Resource, CopySource, App.Management.Tabs,
           ZDOM.Element,
           AccessControl.Owned.Owned,
           App.Undo.UndoSupport,
           ):
    """A common base class for simple, non-container objects."""
    isPrincipiaFolderish=0
    isTopLevelPrincipiaApplicationObject=0
    
    def manage_afterAdd(self, item, container): pass
    def manage_beforeDelete(self, item, container): pass
    def manage_afterClone(self, item): pass

    # The name of this object and the name used to traverse to thie
    # object in a URL:
    id=''

    # Alias id to __name__, which will make tracebacks a good bit nicer:
    __name__=ComputedAttribute(lambda self: self.id)

    # Name, relative to SOFTWARE_URL of icon used to display item
    # in folder listings.
    icon=''

    # Meta type used for selecting all objects of a given type.
    meta_type='simple item'

    # Default title.  
    title=''

    # Default propertysheet info:
    __propsets__=()

    manage_options=(
        App.Undo.UndoSupport.manage_options
        +AccessControl.Owned.Owned.manage_options
        )
    
    # Attributes that must be acquired
    REQUEST=Acquisition.Acquired

    # Allow (reluctantly) access to unprotected attributes
    __allow_access_to_unprotected_subobjects__=1

    getPhysicalRoot=Acquisition.Acquired
    getPhysicalRoot__roles__=()
    

    def title_or_id(self):
        """
        Utility that returns the title if it is not blank and the id
        otherwise.
        """
        title=self.title
        if callable(title):
            title=title()
        if title: return title
        id=self.id
        if callable(id):
            id=id()
        return id

    def title_and_id(self):
        """
        Utility that returns the title if it is not blank and the id
        otherwise.  If the title is not blank, then the id is included
        in parens.
        """
        title=self.title
        if callable(title):
            title=title()
        id=self.id
        if callable(id):
            id=id()
        return title and ("%s (%s)" % (title,id)) or id
    
    def this(self):
        # Handy way to talk to ourselves in document templates.
        return self

    def tpURL(self):
        # My URL as used by tree tag
        url=self.id
        if hasattr(url,'im_func'): url=url()
        return url

    def tpValues(self):
        # My sub-objects as used by the tree tag
        return ()

    _manage_editedDialog=Globals.HTMLFile('editedDialog', globals())
    def manage_editedDialog(self, REQUEST, **args):
        return apply(self._manage_editedDialog,(self, REQUEST), args)

    def raise_standardErrorMessage(
        self, client=None, REQUEST={},
        error_type=None, error_value=None, tb=None,
        error_tb=None, error_message='',
        tagSearch=regex.compile('[a-zA-Z]>').search):

        try:
            if error_type  is None: error_type =sys.exc_info()[0]
            if error_value is None: error_value=sys.exc_info()[1]
            
            # turn error_type into a string            
            if hasattr(error_type, '__name__'):
                error_type=error_type.__name__

            # allow for a few different traceback options
            if tb is None and error_tb is None:
                tb=sys.exc_info()[2]
            if type(tb) is not type('') and (error_tb is None):
                error_tb=pretty_tb(error_type, error_value, tb)
            elif type(tb) is type('') and not error_tb:
                error_tb=tb

            if hasattr(self, '_v_eek'):
                raise error_type, error_value, tb
            self._v_eek=1
   
            if lower(str(error_type)) in ('redirect',):
                raise error_type, error_value, tb

            if not error_message:
                if type(error_value) is InstanceType:
                    s=str(error_value)
                    if tagSearch(s) >= 0:
                        error_message=error_value
                elif (type(error_value) is StringType
                      and tagSearch(error_value) >= 0):
                    error_message=error_value

            if client is None: client=self
            if not REQUEST: REQUEST=self.aq_acquire('REQUEST')

            try:
                if hasattr(client, 'standard_error_message'):
                    s=getattr(client, 'standard_error_message')
                else:
                    client = client.aq_parent
                    s=getattr(client, 'standard_error_message')
                v=HTML.__call__(s, client, REQUEST, error_type=error_type,
                                error_value=error_value,
                                error_tb=error_tb,error_traceback=error_tb,
                                error_message=error_message)
            except: v = error_value or "Sorry, an error occurred"
            raise error_type, v, tb
        finally:
            if hasattr(self, '_v_eek'): del self._v_eek
            tb=None

    def manage(self, URL1):
        " "
        raise 'Redirect', "%s/manage_main" % URL1 

    # This keeps simple items from acquiring their parents
    # objectValues, etc., when used in simple tree tags.
    def objectValues(self, spec=None):
        return ()
    objectIds=objectItems=objectValues

    # FTP support methods
    
    def manage_FTPstat(self,REQUEST):
        "psuedo stat, used by FTP for directory listings"
        from AccessControl.User import nobody
        mode=0100000
        
        # check read permissions
        if (hasattr(self.aq_base,'manage_FTPget') and 
            hasattr(self.manage_FTPget, '__roles__')):
            try:
                if getSecurityManager().validateValue(self.manage_FTPget):
                    mode=mode | 0440
            except: pass
            if nobody.allowed(self.manage_FTPget,
                              self.manage_FTPget.__roles__):
                mode=mode | 0004
                
        # check write permissions
        if hasattr(self.aq_base,'PUT') and hasattr(self.PUT, '__roles__'):
            try:
                if getSecurityManager().validateValue(self.PUT):
                    mode=mode | 0220
            except: pass
            
            if nobody.allowed(self.PUT, self.PUT.__roles__):
                mode=mode | 0002
                
        # get size
        if hasattr(self, 'get_size'):
            size=self.get_size()
        elif hasattr(self,'manage_FTPget'):
            size=len(self.manage_FTPget())
        else:
            size=0
        # get modification time
        mtime=self.bobobase_modification_time().timeTime()
        # get owner and group
        owner=group='Zope'
        for user, roles in self.get_local_roles():
            if 'Owner' in roles:
                owner=user
                break
        return marshal.dumps((mode,0,0,1,owner,group,size,mtime,mtime,mtime))

    def manage_FTPlist(self,REQUEST):
        """Directory listing for FTP. In the case of non-Foldoid objects,
        the listing should contain one object, the object itself."""
        # check to see if we are being acquiring or not
        ob=self
        while 1:
            if App.Common.is_acquired(ob):
                raise ValueError('FTP List not supported on acquired objects')
            if not hasattr(ob,'aq_parent'):
                break
            ob=ob.aq_parent
            
        stat=marshal.loads(self.manage_FTPstat(REQUEST))
        if callable(self.id): id=self.id()
        else: id=self.id
        return marshal.dumps((id,stat))

    def __len__(self):
        return 1

    def absolute_url(self, relative=0):
        id=quote(self.id)
        
        p=getattr(self,'aq_inner', None)
        if p is not None: 
            url=p.aq_parent.absolute_url(relative)
            if url: id=url+'/'+id
            
        return id

    def getPhysicalPath(self):
        '''Returns a path (an immutable sequence of strings)
        that can be used to access this object again
        later, for example in a copy/paste operation.  getPhysicalRoot()
        and getPhysicalPath() are designed to operate together.
        '''
        path = (self.id,)
        
        p = getattr(self,'aq_inner', None)
        if p is not None: 
            path = p.aq_parent.getPhysicalPath() + path

        return path

    unrestrictedTraverse__roles__=()
    def unrestrictedTraverse(self, path, default=_marker, restricted=0):

        if not path: return self

        get=getattr
        N=None
        M=_marker

        if type(path) is StringType: path = split(path,'/')
        else: path=list(path)

        REQUEST={'TraversalRequestNameStack': path}
        path.reverse()
        pop=path.pop

        if not path[-1]:
            # If the path starts with an empty string, go to the root first.
            pop()
            self=self.getPhysicalRoot()
                    
        try:
            object = self
            while path:
                name=pop()

                if name[0] == '_':
                    # Never allowed in a URL.
                    raise 'NotFound', name

                if name=='..':
                    o=getattr(object, 'aq_parent', M)
                    if o is not M:
                        if (restricted and
                            not getSecurityManager().validate(object, object, name, o)):
                            raise 'Unauthorized', name
                        object=o
                        continue

                t=get(object, '__bobo_traverse__', N)
                if t is not N:
                    o=t(REQUEST, name)
                    
                    # Note we pass no container, because we have no
                    # way of knowing what it is
                    if (restricted and not getSecurityManager().validate(object, None, name, o)):
                        raise 'Unauthorized', name
                      
                else:
                    o=get(object, name, M)
                    if o is not M:
                        if restricted:
                            # waaaa
                            if hasattr(get(object,'aq_base',object), name):
                                # value wasn't acquired
                                if not getSecurityManager().validate(object, object, name, o):
                                    raise 'Unauthorized', name
                            else:
                                if not getSecurityManager().validate(object, None, name, o):
                                    raise 'Unauthorized', name
                        
                    else:
                        o=object[name]
                        if (restricted and not getSecurityManager().validate(object, object, None, o)):
                            raise 'Unauthorized', name

                object=o

            return object

        except:
            if default==_marker: raise
            return default

    restrictedTraverse__roles__=()
    def restrictedTraverse(self, path, default=_marker, restricted=0):
        return self.unrestrictedTraverse(path, default, restricted=1)



Globals.default__class_init__(Item)

class Item_w__name__(Item):
    """Mixin class to support common name/id functions"""

    def title_or_id(self):
        """Utility that returns the title if it is not blank and the id
        otherwise."""
        return self.title or self.__name__

    def title_and_id(self):
        """Utility that returns the title if it is not blank and the id
        otherwise.  If the title is not blank, then the id is included
        in parens."""
        t=self.title
        return t and ("%s (%s)" % (t,self.__name__)) or self.__name__

    def _setId(self, id):
        self.__name__=id

    def absolute_url(self, relative=0):
        id=quote(self.__name__)
        
        p=getattr(self,'aq_inner', None)
        if p is not None: 
            url=p.aq_parent.absolute_url(relative)
            if url: id=url+'/'+id
            
        return id

    def getPhysicalPath(self):
        '''Returns a path (an immutable sequence of strings)
        that can be used to access this object again
        later, for example in a copy/paste operation.  getPhysicalRoot()
        and getPhysicalPath() are designed to operate together.
        '''
        path = (self.__name__,)
        
        p = getattr(self,'aq_inner', None)
        if p is not None: 
            path = p.aq_parent.getPhysicalPath() + path
            
        return path


def format_exception(etype,value,tb,limit=None):
    import traceback
    result=['Traceback (innermost last):']
    if limit is None:
        if hasattr(sys, 'tracebacklimit'):
            limit = sys.tracebacklimit
    n = 0
    while tb is not None and (limit is None or n < limit):
        f = tb.tb_frame
        lineno = tb.tb_lineno
        co = f.f_code
        filename = co.co_filename
        name = co.co_name
        locals=f.f_locals
        result.append('  File %s, line %d, in %s'
                      % (filename,lineno,name))
        try: result.append('    (Object: %s)' %
                           locals[co.co_varnames[0]].__name__)
        except: pass
        try: result.append('    (Info: %s)' %
                           str(locals['__traceback_info__']))
        except: pass
        tb = tb.tb_next
        n = n+1
    result.append(join(traceback.format_exception_only(etype, value),' '))
    return result

def pretty_tb(t,v,tb):
    tb=format_exception(t,v,tb,200)
    tb=join(tb,'\n')
    return tb

class SimpleItem(Item, Globals.Persistent,
                 Acquisition.Implicit,
                 AccessControl.Role.RoleManager,
                 ):
    # Blue-plate special, Zope Masala
    """Mix-in class combining the most common set of basic mix-ins
    """

    manage_options=Item.manage_options+(
        {'label':'Security',   'action':'manage_access'},
        )
 
    __ac_permissions__=(('View', ()),)
