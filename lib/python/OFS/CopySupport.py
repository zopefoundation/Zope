__doc__="""Copy interface"""
__version__='$Revision: 1.19 $'[11:-2]

import sys, Globals, Moniker, tempfile
from marshal import loads, dumps
from urllib import quote, unquote
from zlib import compress, decompress
from App.Dialogs import MessageDialog


CopyError='Copy Error'

class CopyContainer:
    # Interface for containerish objects which allow cut/copy/paste

    def manage_cutObjects(self, ids, REQUEST=None):
        """Put a reference to the objects named in ids in the clip board"""
        if type(ids) is type(''):
            ids=[ids]
        oblist=[]
        for id in ids:
            ob=getattr(self, id)
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
            ob=getattr(self, id)
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
                id=_get_id(self, absattr(ob.id))
                ob=ob._getCopy(self)
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
                self._setObject(id, ob)
                ob=ob.__of__(self)            
                ob._setId(id)
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
        ob=getattr(self, id)
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
	# Return true if clipboard data seems valid.
	try:    cp=_cb_decode(self.REQUEST['__cp'])
	except: return 0
        return 1

    def cb_dataItems(self):
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
            if hasattr(self, method_name):
                meth=getattr(self, method_name)
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
    # Interface for objects which allow themselves to be copied.
    
    def _canCopy(self, op=0):
        # Called to make sure this object is copyable. The op var
        # is 0 for a copy, 1 for a move.
        return 1

    def _notifyOfCopyTo(self, container, op=0):
        # Overide this to be pickly about where you go! If you dont
        # want to go there, raise an exception. The op variable is
        # 0 for a copy, 1 for a move.
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
        if not (hasattr(self, '_canCopy') and self._canCopy(0)):
            return 0
        if hasattr(self, '_p_jar') and self._p_jar is None:
            return 0
        return 1

    def cb_isMoveable(self):
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
    if id[8:]=='copy_of_':
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




############################################################################## 
#
# $Log: CopySupport.py,v $
# Revision 1.19  1998/08/14 20:54:44  brian
# Readded Find support that got overwritten somehow
#
# Revision 1.18  1998/08/14 16:46:35  brian
# Added multiple copy, paste, rename
#

