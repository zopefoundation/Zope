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
__doc__="""Copy interface"""
__version__='$Revision: 1.31 $'[11:-2]

import sys, string, Globals, Moniker, tempfile, ExtensionClass
from marshal import loads, dumps
from urllib import quote, unquote
from zlib import compress, decompress
from App.Dialogs import MessageDialog


CopyError='Copy Error'

_marker=[]
class CopyContainer(ExtensionClass.Base):
    """Interface for containerish objects which allow cut/copy/paste"""

    __ac_permissions__=(
        ('View management screens',
         ('manage_cutObjects', 'manage_copyObjects', 'manage_pasteObjects',
          'manage_renameForm', 'manage_renameObject',)),
        )


    # The following three methods should be overridden to store sub-objects
    # as non-attributes.
    def _setOb(self, id, object): setattr(self, id, object)
    def _delOb(self, id): delattr(self, id)
    def _getOb(self, id, default=_marker):
        if hasattr(self, 'aq_base'): self=self.aq_base
        if default is _marker: return getattr(self, id)
        try: return getattr(self, id)
        except: return default


    def manage_CopyContainerFirstItem(self, REQUEST):
        return self._getOb(REQUEST['ids'][0])        

    def manage_cutObjects(self, ids, REQUEST=None):
        """Put a reference to the objects named in ids in the clip board"""
        if type(ids) is type(''):
            ids=[ids]
        oblist=[]
        for id in ids:
            ob=self._getOb(id)
            if not ob.cb_isMoveable():
                raise CopyError, eNotSupported % id
            m=Moniker.Moniker(ob)
            oblist.append((m.jar, m.ids))
        cp=(1, oblist)
        cp=_cb_encode(cp)
        if REQUEST is not None:
            resp=REQUEST['RESPONSE']
            resp.setCookie('__cp', cp, path='%s' % REQUEST['SCRIPT_NAME'])
            return self.manage_main(self, REQUEST, cb_dataValid=1)
        return cp
    
    def manage_copyObjects(self, ids, REQUEST=None, RESPONSE=None):
        """Put a reference to the objects named in ids in the clip board"""
        if type(ids) is type(''):
            ids=[ids]
        oblist=[]
        for id in ids:
            ob=self._getOb(id)
            if not ob.cb_isCopyable():
                raise CopyError, eNotSupported % id
            m=Moniker.Moniker(ob)
            oblist.append((m.jar, m.ids))
        cp=(0, oblist)
        cp=_cb_encode(cp)
        if REQUEST is not None:
            resp=REQUEST['RESPONSE']
            resp.setCookie('__cp', cp, path='%s' % REQUEST['SCRIPT_NAME'])
            return self.manage_main(self, REQUEST, cb_dataValid=1)
        return cp

    def manage_pasteObjects(self, cb_copy_data=None, REQUEST=None):
        """Paste previously copied objects into the current object.
           If calling manage_pasteObjects from python code, pass
           the result of a previous call to manage_cutObjects or
           manage_copyObjects as the first argument."""
        cp=None
        if cb_copy_data is not None:
            cp=cb_copy_data
        else:
            if REQUEST and REQUEST.has_key('__cp'):
                cp=REQUEST['__cp']
        if cp is None:
            raise CopyError, eNoData
        
        try:    cp=_cb_decode(cp)
        except: raise CopyError, eInvalid

        oblist=[]
        m=Moniker.Moniker()
        op=cp[0]
        for j, d in cp[1]:
            m.jar=j
            m.ids=d
            try: ob=m.bind()
            except: raise CopyError, eNotFound
            self._verifyObjectPaste(ob, REQUEST)
            try:    ob._notifyOfCopyTo(self, op=op)
            except: raise CopyError, MessageDialog(
                          title='Copy Error',
                          message=sys.exc_value,
                          action ='manage_main')
            oblist.append(ob)

        if op==0:
            # Copy operation
            for ob in oblist:
                if not ob.cb_isCopyable():
                    raise CopyError, eNotSupported % absattr(ob.id)
                ob=ob._getCopy(self)
                id=_get_id(self, absattr(ob.id))
                ob._setId(id)
                self._setObject(id, ob)
                ob=ob.__of__(self)
                ob._postCopy(self, op=0)

            if REQUEST is not None:
                return self.manage_main(self, REQUEST, update_menu=1,
                                        cb_dataValid=1)

        if op==1:
            # Move operation
            for ob in oblist:
                id=absattr(ob.id)
                if not ob.cb_isMoveable():
                    raise CopyError, eNotSupported % id
                ob.aq_parent._delObject(id)
                if hasattr(ob, 'aq_base'):
                    ob=ob.aq_base
                id=_get_id(self, id)
                ob._setId(id)
                self._setObject(id, ob)
                ob=ob.__of__(self)            
                ob._postCopy(self, op=1)

            if REQUEST is not None:
                REQUEST['RESPONSE'].setCookie('cp_', 'deleted',
                                    path='%s' % REQUEST['SCRIPT_NAME'],
                                    expires='Wed, 31-Dec-97 23:59:59 GMT')
                return self.manage_main(self, REQUEST, update_menu=1,
                                        cb_dataValid=0)
        return ''


    manage_renameForm=Globals.HTMLFile('renameForm', globals())

    def manage_renameObject(self, id, new_id, REQUEST=None):
        """Rename a particular sub-object"""
        try: self._checkId(new_id)
        except: raise CopyError, MessageDialog(
                      title='Invalid Id',
                      message=sys.exc_value,
                      action ='manage_main')
        ob=self._getOb(id)
        if not ob.cb_isMoveable():
            raise CopyError, eNotSupported % id            
        self._verifyObjectPaste(ob, REQUEST)
        try:    ob._notifyOfCopyTo(self, op=1)
        except: raise CopyError, MessageDialog(
                      title='Rename Error',
                      message=sys.exc_value,
                      action ='manage_main')
        self._delObject(id)
        if hasattr(ob, 'aq_base'):
            ob=ob.aq_base
        self._setObject(new_id, ob)
        ob=ob.__of__(self)            
        ob._setId(new_id)
        ob._postCopy(self, op=1)
        if REQUEST is not None:
            return self.manage_main(self, REQUEST, update_menu=1)
        return None

    # Why did we give this a manage_ prefix if its really
    # supposed to be public since it does its own auth ?
    #
    # Because it's still a "management" function.
    manage_clone__roles__=None
    def manage_clone(self, ob, id, REQUEST=None):
        """Clone an object, creating a new object with the given id."""
        if not ob.cb_isCopyable():
            raise CopyError, eNotSupported % absattr(ob.id)            
        try: self._checkId(id)
        except: raise CopyError, MessageDialog(
                      title='Invalid Id',
                      message=sys.exc_value,
                      action ='manage_main')
        self._verifyObjectPaste(ob, REQUEST)
        try:    ob._notifyOfCopyTo(self, op=0)
        except: raise CopyError, MessageDialog(
                      title='Rename Error',
                      message=sys.exc_value,
                      action ='manage_main')
        ob=ob._getCopy(self)
        ob._setId(id)
        self._setObject(id, ob)
        ob=ob.__of__(self)
        ob._postCopy(self, op=0)
        return ob

    def cb_dataValid(self):
        "Return true if clipboard data seems valid."
        try:    cp=_cb_decode(self.REQUEST['__cp'])
        except: return 0
        return 1

    def cb_dataItems(self):
        "List of objects in the clip board"
        try:    cp=_cb_decode(self.REQUEST['__cp'])
        except: return []
        oblist=[]
        m=Moniker.Moniker()
        op=cp[0]
        for j, d in cp[1]:
            m.jar=j
            m.ids=d
            oblist.append(m.bind())
        return oblist

    validClipData=cb_dataValid

    def _verifyObjectPaste(self, ob, REQUEST):
        if not hasattr(ob, 'meta_type'):
            raise CopyError, MessageDialog(
                  title='Not Supported',
                  message='The object <EM>%s</EM> does not support this ' \
                          'operation' % absattr(ob.id),
                  action='manage_main')
        mt=ob.meta_type
        if not hasattr(self, 'all_meta_types'):
            raise CopyError, MessageDialog(
                  title='Not Supported',
                  message='Cannot paste into this object.',
                  action='manage_main')

        method_name=None
        meta_types=absattr(self.all_meta_types)
        for d in meta_types:
            if d['name']==mt:
                method_name=d['action']
                break
            
        if method_name is not None:

            meth=None
            if hasattr(self, method_name):
                meth=self._getOb(method_name)
            else:
                # Handle strange names that come from the Product
                # machinery ;(
                mn=string.split(method_name, '/')
                if len(mn) > 1:
                    pname= mn[1]
                    product=self.manage_addProduct[pname]
                    fname=mn[2]
                    factory=getattr(product, fname)
                    try: meth=getattr(factory, factory.initial)
                    except: meth=factory

            if hasattr(meth, '__roles__'):
                roles=meth.__roles__
                user=REQUEST.get('AUTHENTICATED_USER', None)
                __traceback_info__=method_name, user
                if (not hasattr(user, 'hasRole') or
                    not user.hasRole(None, roles)):
                    raise 'Unauthorized', (
                          """You are not authorized to perform this
                             operation."""
                          )
                return
        raise CopyError, MessageDialog(
              title='Not Supported',
              message='The object <EM>%s</EM> does not support this ' \
                      'operation' % absattr(ob.id),
              action='manage_main')

Globals.default__class_init__(CopyContainer)



class CopySource:
    """Interface for objects which allow themselves to be copied."""
    
    def _canCopy(self, op=0):
        """Called to make sure this object is copyable. The op var
        is 0 for a copy, 1 for a move."""
        return 1

    def _notifyOfCopyTo(self, container, op=0):
        """Overide this to be pickly about where you go! If you dont
        want to go there, raise an exception. The op variable is
        0 for a copy, 1 for a move."""
        pass

    def _getCopy(self, container):
        # Ask an object for a new copy of itself.
        f=tempfile.TemporaryFile()
        self._p_jar.export_file(self,f)
        f.seek(0)
        ob=container._p_jar.import_file(f)
        f.close()
        return ob

    def _postCopy(self, container, op=0):
        # Called after the copy is finished to accomodate special cases.
        # The op var is 0 for a copy, 1 for a move.
        pass
    
    def _setId(self, id):
        # Called to set the new id of a copied object.
        self.id=id

    def cb_isCopyable(self):
        """Is object copyable? Returns 0 or 1"""
        if not (hasattr(self, '_canCopy') and self._canCopy(0)):
            return 0
        if hasattr(self, '_p_jar') and self._p_jar is None:
            return 0
        return 1

    def cb_isMoveable(self):
        """Is object moveable? Returns 0 or 1"""
        if not (hasattr(self, '_canCopy') and self._canCopy(1)):
            return 0
        if hasattr(self, '_p_jar') and self._p_jar is None:
            return 0
        try:    n=self.aq_parent._reserved_names
        except: n=()
        if absattr(self.id) in n:
            return 0
        return 1


def absattr(attr):
    if callable(attr): return attr()
    return attr

def _get_id(ob, id):
    try: ob=ob.aq_base
    except: pass
    n=0
    if (len(id) > 8) and (id[8:]=='copy_of_'):
        n=1
    while (hasattr(ob, id)):
        id='copy%s_of_%s' % (n and n+1 or '', id)
        n=n+1
    return id



def _cb_encode(d):
    return quote(compress(dumps(d), 9))

def _cb_decode(s):
    return loads(decompress(unquote(s)))




fMessageDialog=Globals.HTML("""
<HTML>
<HEAD>
<TITLE><!--#var title--></TITLE>
</HEAD>
<BODY BGCOLOR="#FFFFFF">
<FORM ACTION="<!--#var action-->" METHOD="GET" 
      <!--#if target-->
      TARGET="<!--#var target-->"
      <!--#/if target-->>
<TABLE BORDER="0" WIDTH="100%%" CELLPADDING="10">
<TR>
  <TD VALIGN="TOP">
  <BR>
  <CENTER><B><FONT SIZE="+6" COLOR="#77003B">!</FONT></B></CENTER>
  </TD>
  <TD VALIGN="TOP">
  <BR><BR>
  <CENTER>
  <!--#var message-->
  </CENTER>
  </TD>
</TR>
<TR>
  <TD VALIGN="TOP">
  </TD>
  <TD VALIGN="TOP">
  <CENTER>
  <INPUT TYPE="SUBMIT" VALUE="   Ok   ">
  </CENTER>
  </TD>
</TR>
</TABLE>
</FORM>
</BODY></HTML>""", target='', action='manage_main', title='Changed')


eNoData=MessageDialog(
        title='No Data',
        message='No clipboard data found.',
        action ='manage_main',)

eInvalid=MessageDialog(
         title='Clipboard Error',
         message='The data in the clipboard could not be read, possibly due ' \
         'to cookie data being truncated by your web browser. Try copying ' \
         'fewer objects.',
         action ='manage_main',)

eNotFound=MessageDialog(
          title='Item Not Found',
          message='One or more items referred to in the clipboard data was ' \
          'not found. The item may have been moved or deleted after you ' \
          'copied it.',
          action ='manage_main',)

eNotSupported=fMessageDialog(
              title='Not Supported',
              message='The item <EM>%s</EM> does not support this operation.',
              action ='manage_main',)
