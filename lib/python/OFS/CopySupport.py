"""Copy interface"""

__version__='$Revision: 1.15 $'[11:-2]

import Globals, Moniker, rPickle, tempfile
from cPickle import loads, dumps
from urllib import quote, unquote
from App.Dialogs import MessageDialog

rPickle.register('OFS.Moniker', 'Moniker', Moniker.Moniker)

class CopyContainer:
    # Interface for containerish objects which allow
    # objects to be copied into them.

    pasteDialog=Globals.HTMLFile('pasteDialog', globals())

    def _getMoniker(self):
        # Ask an object to return a moniker for itself.
	return Moniker.Moniker(self)

    def validClipData(self):
	# Return true if clipboard data is valid.
	try:    moniker=rPickle.loads(unquote(self.REQUEST['clip_data']))
	except: return 0

	# Check for old versions of cookie so users dont need to
	# restart browser after upgrading - just expire the old
	# cookie.
	if not hasattr(moniker, 'op'):
	    self.REQUEST['RESPONSE'].setCookie('clip_data', 'deleted',
				     path='%s' % self.REQUEST['SCRIPT_NAME'],
				     expires='Wed, 31-Dec-97 23:59:59 GMT')
	    self.REQUEST['validClipData']=0
	    return 0

	v=self.REQUEST['validClipData']=moniker.assert()
	return v

    def pasteFromClipboard(self, clip_id='', clip_data='', REQUEST=None):
	""" """
	if not clip_data: return eNoData

	try:    moniker=rPickle.loads(unquote(clip_data))
	except: return eInvalid

	if not clip_id:
	    return self.pasteDialog(self,REQUEST,bad=0,moniker=(moniker,))

	try:    self._checkId(clip_id)
	except: return self.pasteDialog(self,REQUEST,bad=1,moniker=(moniker,))

	return self.manage_paste(moniker, clip_id, REQUEST)


    def manage_paste(self, moniker, clip_id, REQUEST=None):
        """ """
	try:    obj=moniker.bind()
	except: return eNotFound

	if moniker.op == 0:
	    # Copy operation

	    obj=obj._getCopy(self)
	    obj._setId(clip_id)
	    self._setObject(clip_id, obj)
	    obj._postCopy(self)

	    if REQUEST is not None:
		return self.manage_main(self, REQUEST, update_menu=1)
	    return ''

	if moniker.op==1:
	    # Move operation
	    prev_id=Moniker.absattr(obj.id)

            # Check for special object!
	    try:    r=obj.aq_parent._reserved_names
	    except: r=()
            if prev_id in special:
                raise 'NotSupported', eNotSupported
            
	    obj.aq_parent._delObject(prev_id)
            if hasattr(obj, 'aq_base'):
                obj=obj.aq_base
	    self._setObject(clip_id, obj)
	    obj=obj.__of__(self)            
            obj._setId(clip_id)
            obj._postMove(self)
	    if REQUEST is not None:
		# Remove cookie after a move
		REQUEST['RESPONSE'].setCookie('clip_data', 'deleted',
				    path='%s' % REQUEST['SCRIPT_NAME'],
				    expires='Wed, 31-Dec-97 23:59:59 GMT')
		return self.manage_main(self, REQUEST, update_menu=1,
					validClipData=0)
	    return ''


Globals.default__class_init__(CopyContainer)


class CopySource:
    # Interface for objects which allow themselves to be copied.

    def _getMoniker(self):
        # Ask an object to return a moniker for itself.
	return Moniker.Moniker(self)

    def _getCopy(self, container):
	# Ask an object for a new copy of itself.
	f=tempfile.TemporaryFile()
	self._p_jar.export_file(self,f)
	f.seek(0)
	r=container._p_jar.import_file(f)
	f.close()
	return r

    def _postCopy(self, container):
	# Called after the copy is finished to accomodate special cases
	pass

    def _postMove(self, container):
        # Called after a move is finished to accomodate special cases
        pass
    
    def _setId(self, id):
	# Called to set the new id of a copied object.
	self.id=id

    def copyToClipboard(self, REQUEST):
        """ """
	# Set a cookie containing pickled moniker
	try:    m=self._getMoniker()
	except: return eNotSupported
	m.op=0
	REQUEST['RESPONSE'].setCookie('clip_data',
			    quote(dumps(m, 1)),
			    path='%s' % REQUEST['SCRIPT_NAME'])

    def cutToClipboard(self, REQUEST):
        """ """
	# Set a cookie containing pickled moniker
	try:    m=self._getMoniker()
	except: return eNotSupported
	m.op=1
	REQUEST['RESPONSE'].setCookie('clip_data',
			    quote(dumps(m, 1)),
			    path='%s' % REQUEST['SCRIPT_NAME'])





# Predefined errors

eNoData=Globals.MessageDialog(
        title='No Data',
	message='No clipboard data to be pasted',
	action ='./manage_main',)

eInvalid=Globals.MessageDialog(
	 title='Clipboard Error',
	 message='Clipboard data could not be read ' \
		 'or is not supported in this installation',
	 action ='./manage_main',)

eNotFound=Globals.MessageDialog(
	  title='Clipboard Error',
	  message='The item referenced by the ' \
	          'clipboard data was not found',
	  action ='./manage_main',)

eNotSupported=Globals.MessageDialog(
	      title='Not Supported',
	      message='Operation not supported for the selected item',
	      action ='./manage_main',)



