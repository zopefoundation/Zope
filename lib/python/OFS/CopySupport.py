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
__version__='$Revision: 1.72 $'[11:-2]

import sys, string, Globals, Moniker, tempfile, ExtensionClass
from marshal import loads, dumps
from urllib import quote, unquote
from zlib import compress, decompress
from App.Dialogs import MessageDialog
from AccessControl import getSecurityManager
from Acquisition import aq_base, aq_inner, aq_parent


CopyError='Copy Error'

_marker=[]
class CopyContainer(ExtensionClass.Base):
    """Interface for containerish objects which allow cut/copy/paste"""

    __ac_permissions__=(
        ('View management screens',
         ('manage_cutObjects', 'manage_copyObjects', 'manage_pasteObjects',
          'manage_renameForm', 'manage_renameObject', 'manage_renameObjects',)),
        )


    # The following three methods should be overridden to store sub-objects
    # as non-attributes.
    def _setOb(self, id, object): setattr(self, id, object)
    def _delOb(self, id): delattr(self, id)
    def _getOb(self, id, default=_marker):
        self = aq_base(self)
        if default is _marker: return getattr(self, id)
        try: return getattr(self, id)
        except: return default


    def manage_CopyContainerFirstItem(self, REQUEST):
        return self._getOb(REQUEST['ids'][0])

    def manage_CopyContainerAllItems(self, REQUEST):
        return map(lambda i, s=self: s._getOb(i), tuple(REQUEST['ids']))

    def manage_cutObjects(self, ids=None, REQUEST=None):
        """Put a reference to the objects named in ids in the clip board"""
        if ids is None and REQUEST is not None:
            return eNoItemsSpecified
        elif ids is None:
            raise ValueError, 'ids must be specified'

        if type(ids) is type(''):
            ids=[ids]
        oblist=[]
        for id in ids:
            ob=self._getOb(id)
            if not ob.cb_isMoveable():
                raise CopyError, eNotSupported % id
            m=Moniker.Moniker(ob)
            oblist.append(m.dump())
        cp=(1, oblist)
        cp=_cb_encode(cp)
        if REQUEST is not None:
            resp=REQUEST['RESPONSE']
            resp.setCookie('__cp', cp, path='%s' % cookie_path(REQUEST))
            REQUEST['__cp'] = cp
            return self.manage_main(self, REQUEST)
        return cp
    
    def manage_copyObjects(self, ids=None, REQUEST=None, RESPONSE=None):
        """Put a reference to the objects named in ids in the clip board"""
        if ids is None and REQUEST is not None:
            return eNoItemsSpecified
        elif ids is None:
            raise ValueError, 'ids must be specified'

        if type(ids) is type(''):
            ids=[ids]
        oblist=[]
        for id in ids:
            ob=self._getOb(id)
            if not ob.cb_isCopyable():
                raise CopyError, eNotSupported % id
            m=Moniker.Moniker(ob)
            oblist.append(m.dump())
        cp=(0, oblist)
        cp=_cb_encode(cp)
        if REQUEST is not None:
            resp=REQUEST['RESPONSE']
            resp.setCookie('__cp', cp, path='%s' % cookie_path(REQUEST))
            REQUEST['__cp'] = cp
            return self.manage_main(self, REQUEST)
        return cp

    def _get_id(self, id):
        # Allow containers to override the generation of
        # object copy id by attempting to call its _get_id
        # method, if it exists.
        n=0
        if (len(id) > 8) and (id[8:]=='copy_of_'):
            n=1
        orig_id=id
        while 1:
            if self._getOb(id, None) is None:
                return id
            id='copy%s_of_%s' % (n and n+1 or '', orig_id)
            n=n+1

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
        op=cp[0]
        app = self.getPhysicalRoot()

        for mdata in cp[1]:
            m = Moniker.loadMoniker(mdata)
            try: ob = m.bind(app)
            except: raise CopyError, eNotFound
            self._verifyObjectPaste(ob)
            oblist.append(ob)

        if op==0:
            # Copy operation
            for ob in oblist:
                if not ob.cb_isCopyable():
                    raise CopyError, eNotSupported % ob.getId()
                try:    ob._notifyOfCopyTo(self, op=0)
                except: raise CopyError, MessageDialog(
                    title='Copy Error',
                    message=sys.exc_info()[1],
                    action ='manage_main')
                ob=ob._getCopy(self)
                id=self._get_id(ob.getId())
                ob._setId(id)
                self._setObject(id, ob)
                ob = self._getOb(id)
                ob.manage_afterClone(ob)

            if REQUEST is not None:
                return self.manage_main(self, REQUEST, update_menu=1,
                                        cb_dataValid=1)

        if op==1:
            # Move operation
            for ob in oblist:
                id=ob.getId()
                if not ob.cb_isMoveable():
                    raise CopyError, eNotSupported % id
                try:    ob._notifyOfCopyTo(self, op=1)
                except: raise CopyError, MessageDialog(
                    title='Move Error',
                    message=sys.exc_info()[1],
                    action ='manage_main')
                if not sanity_check(self, ob):
                    raise CopyError, 'This object cannot be pasted into itself'

                # try to make ownership explicit so that it gets carried
                # along to the new location if needed.
                ob.manage_changeOwnershipType(explicit=1)
                
                aq_parent(aq_inner(ob))._delObject(id)
                ob = aq_base(ob)
                id=self._get_id(id)
                ob._setId(id)

                self._setObject(id, ob, set_owner=0)

                # try to make ownership implicit if possible
                ob=self._getOb(id)
                ob.manage_changeOwnershipType(explicit=0)

            if REQUEST is not None:
                REQUEST['RESPONSE'].setCookie('__cp', 'deleted',
                                    path='%s' % cookie_path(REQUEST),
                                    expires='Wed, 31-Dec-97 23:59:59 GMT')
                REQUEST['__cp'] = None
                return self.manage_main(self, REQUEST, update_menu=1,
                                        cb_dataValid=0)
        return ''


    manage_renameForm=Globals.DTMLFile('dtml/renameForm', globals())

    def manage_renameObjects(self, ids=[], new_ids=[], REQUEST=None):
        """Rename several sub-objects"""
        if len(ids) != len(new_ids):
            raise 'Bad Request','Please rename each listed object.'
        for i in range(len(ids)):
            if ids[i] != new_ids[i]:
                self.manage_renameObject(ids[i], new_ids[i], REQUEST)
        if REQUEST is not None:
            return self.manage_main(self, REQUEST, update_menu=1)
        return None

    def manage_renameObject(self, id, new_id, REQUEST=None):
        """Rename a particular sub-object"""
        try: self._checkId(new_id)
        except: raise CopyError, MessageDialog(
                      title='Invalid Id',
                      message=sys.exc_info()[1],
                      action ='manage_main')
        ob=self._getOb(id)
        if not ob.cb_isMoveable():
            raise CopyError, eNotSupported % id            
        self._verifyObjectPaste(ob)
        try:    ob._notifyOfCopyTo(self, op=1)
        except: raise CopyError, MessageDialog(
                      title='Rename Error',
                      message=sys.exc_info()[1],
                      action ='manage_main')
        self._delObject(id)
        ob = aq_base(ob)
        ob._setId(new_id)
        
        # Note - because a rename always keeps the same context, we
        # can just leave the ownership info unchanged.
        self._setObject(new_id, ob, set_owner=0)

        if REQUEST is not None:
            return self.manage_main(self, REQUEST, update_menu=1)
        return None

    # Why did we give this a manage_ prefix if its really
    # supposed to be public since it does its own auth ?
    #
    # Because it's still a "management" function.
    manage_clone__roles__=None
    def manage_clone(self, ob, id, REQUEST=None):
        # Clone an object, creating a new object with the given id.
        if not ob.cb_isCopyable():
            raise CopyError, eNotSupported % ob.getId()
        try: self._checkId(id)
        except: raise CopyError, MessageDialog(
                      title='Invalid Id',
                      message=sys.exc_info()[1],
                      action ='manage_main')
        self._verifyObjectPaste(ob)
        try:    ob._notifyOfCopyTo(self, op=0)
        except: raise CopyError, MessageDialog(
                      title='Clone Error',
                      message=sys.exc_info()[1],
                      action ='manage_main')
        ob=ob._getCopy(self)
        ob._setId(id)
        self._setObject(id, ob)
        ob=ob.__of__(self)
        #ob._postCopy(self, op=0)
        return ob

    def cb_dataValid(self):
        # Return true if clipboard data seems valid.
        try:    cp=_cb_decode(self.REQUEST['__cp'])
        except: return 0
        return 1

    def cb_dataItems(self):
        # List of objects in the clip board
        try:    cp=_cb_decode(self.REQUEST['__cp'])
        except: return []
        oblist=[]

        app = self.getPhysicalRoot()
        for mdata in cp[1]:
            m = Moniker.loadMoniker(mdata)
            oblist.append(m.bind(app))
        return oblist

    validClipData=cb_dataValid

    def _verifyObjectPaste(self, object, validate_src=1):
        # Verify whether the current user is allowed to paste the
        # passed object into self. This is determined by checking
        # to see if the user could create a new object of the same
        # meta_type of the object passed in and checking that the
        # user actually is allowed to access the passed in object
        # in its existing context.
        #
        # Passing a false value for the validate_src argument will skip
        # checking the passed in object in its existing context. This is
        # mainly useful for situations where the passed in object has no 
        # existing context, such as checking an object during an import
        # (the object will not yet have been connected to the acquisition
        # heirarchy).
        if not hasattr(object, 'meta_type'):
            raise CopyError, MessageDialog(
                  title='Not Supported',
                  message='The object <EM>%s</EM> does not support this ' \
                          'operation' % absattr(object.id),
                  action='manage_main')
        mt=object.meta_type
        if not hasattr(self, 'all_meta_types'):
            raise CopyError, MessageDialog(
                  title='Not Supported',
                  message='Cannot paste into this object.',
                  action='manage_main')

        method_name=None
        mt_permission=None
        meta_types=absattr(self.all_meta_types)
        for d in meta_types:
            if d['name']==mt:
                method_name=d['action']
                mt_permission=d.get( 'permission', None )
                break

        if mt_permission is not None:
            if getSecurityManager().checkPermission( mt_permission, self ):
                if not validate_src:
                    return
                # Ensure the user is allowed to access the object on the
                # clipboard.
                try:    parent=aq_parent(aq_inner(object))
                except: parent=None
                if getSecurityManager().validate(None, parent, None, object):
                    return
                raise 'Unauthorized', absattr(object.id)
            else:
                raise 'Unauthorized', mt_permission
        #
        #   XXX:    Ancient cruft, left here in true co-dependent fashion
        #           to keep from breaking old products which don't put
        #           permissions on their metadata registry entries.
        #
        if method_name is not None:
            meth=self.unrestrictedTraverse(method_name)
            if hasattr(meth, 'im_self'):
                parent = meth.im_self
            else:
                try:    parent=aq_parent(aq_inner(meth))
                except: parent=None
            if getSecurityManager().validate(None, parent, None, meth):
                # Ensure the user is allowed to access the object on the
                # clipboard.
                if not validate_src:
                    return
                try:    parent=aq_parent(aq_inner(object))
                except: parent=None
                if getSecurityManager().validate(None, parent, None, object):
                    return
                raise 'Unauthorized', absattr(object.id)
            else:
                raise 'Unauthorized', method_name

        raise CopyError, MessageDialog(
              title='Not Supported',
              message='The object <EM>%s</EM> does not support this ' \
                      'operation' % absattr(object.id),
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
        self._p_jar.exportFile(self._p_oid,f)
        f.seek(0)
        ob=container._p_jar.importFile(f)
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
        # Is object copyable? Returns 0 or 1
        if not (hasattr(self, '_canCopy') and self._canCopy(0)):
            return 0
        if hasattr(self, '_p_jar') and self._p_jar is None:
            return 0
        return 1

    def cb_isMoveable(self):
        # Is object moveable? Returns 0 or 1
        if not (hasattr(self, '_canCopy') and self._canCopy(1)):
            return 0
        if hasattr(self, '_p_jar') and self._p_jar is None:
            return 0
        try:    n=aq_parent(aq_inner(self))._reserved_names
        except: n=()
        if absattr(self.id) in n:
            return 0
        return 1



def sanity_check(c, ob):
    # This is called on cut/paste operations to make sure that
    # an object is not cut and pasted into itself or one of its
    # subobjects, which is an undefined situation.
    ob = aq_base(ob)
    while 1:
        if aq_base(c) is ob:
            return 0
        inner = aq_inner(c)
        if aq_parent(inner) is None:
            return 1
        c = aq_parent(inner)

def absattr(attr):
    if callable(attr): return attr()
    return attr

def _cb_encode(d):
    return quote(compress(dumps(d), 9))

def _cb_decode(s):
    return loads(decompress(unquote(s)))

def cookie_path(request):
    # Return a "path" value for use in a cookie that refers
    # to the root of the Zope object space.
    return request['BASEPATH1'] or "/"



fMessageDialog=Globals.HTML("""
<HTML>
<HEAD>
<TITLE><dtml-var title></TITLE>
</HEAD>
<BODY BGCOLOR="#FFFFFF">
<FORM ACTION="<dtml-var action>" METHOD="GET" <dtml-if
 target>TARGET="<dtml-var target>"</dtml-if>>
<TABLE BORDER="0" WIDTH="100%%" CELLPADDING="10">
<TR>
  <TD VALIGN="TOP">
  <BR>
  <CENTER><B><FONT SIZE="+6" COLOR="#77003B">!</FONT></B></CENTER>
  </TD>
  <TD VALIGN="TOP">
  <BR><BR>
  <CENTER>
  <dtml-var message>
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

eNoItemsSpecified=MessageDialog(
                  title='No items specified',
                  message='You must select one or more items to perform ' \
                  'this operation.',
                  action ='manage_main'
                  )
