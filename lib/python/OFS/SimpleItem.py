#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1997 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved. 
#
############################################################################## 

'''This module implements a simple item mix-in for objects that have a
very simple (e.g. one-screen) management interface, like documents,
Aqueduct database adapters, etc.

This module can also be used as a simple template for implementing new
item types. 

$Id: SimpleItem.py,v 1.22 1998/08/03 13:32:39 jim Exp $'''
__version__='$Revision: 1.22 $'[11:-2]

import regex, sys, Globals, App.Management
from DateTime import DateTime
from CopySupport import CopySource
from string import join, lower

HTML=Globals.HTML

class Item(CopySource, App.Management.Tabs):

    isPrincipiaFolderish=0
    isTopLevelPrincipiaApplicationObject=0

    # Name, relative to SOFTWARE_URL of icon used to display item
    # in folder listings.
    icon='Product/icon'

    # Meta type used for selecting all objects of a given type.
    meta_type='simple item'

    # Default title.  
    title=''

    manage_info   =Globals.HTMLFile('App/manage_info')
    manage_options=({'icon':'', 'label':'Manage',
		     'action':'manage_main', 'target':'manage_main',
	            },
		    {'icon':'', 'label':'Access Control',
		     'action':'manage_access', 'target':'manage_main',
		    },
		    {'icon':'', 'label':'Undo',
		     'action':'manage_UndoForm','target':'manage_main',
		    },
		   )

    # Utility that returns the title if it is not blank and the id
    # otherwise.
    def title_or_id(self):
	return self.title or self.id

    # Utility that returns the title if it is not blank and the id
    # otherwise.  If the title is not blank, then the id is included
    # in parens.
    def title_and_id(self):
	t=self.title
	return t and ("%s (%s)" % (t,self.id)) or self.id

    
    # Handy way to talk to ourselves in document templates.
    def this(self):
	return self

    # Interact with tree tag
    def tpURL(self):
	url=self.id
	if hasattr(url,'im_func'): url=url()
	return url

    def tpValues(self): return ()

    _manage_editedDialog=Globals.HTMLFile('editedDialog', globals())
    def manage_editedDialog(self, REQUEST, **args):
	return apply(self._manage_editedDialog,(self, REQUEST), args)

    def raise_standardErrorMessage(self, client=None, REQUEST={},
				   error_type=None, error_value=None, tb=None,
				   error_tb=None, error_message=''):
	try:
	    if not error_type: error_type=sys.exc_type
	    if not error_value: error_value=sys.exc_value
	    
	    # allow for a few different traceback options
	    if tb is None and (error_tb is None):
		tb=sys.exc_traceback
	    if type(tb) is not type('') and (error_tb is None):
		error_tb=pretty_tb(error_type, error_value, tb)
	    elif type(tb) is type('') and not error_tb:
		error_tb=tb

	    if lower(error_type) in ('redirect',):
		raise error_type, error_value, tb
	    if (type(error_value) is type('') and not error_message and
		regex.search('[a-zA-Z]>', error_value) > 0):
		error_message=error_value

	    if client is None: client=self
	    if not REQUEST: REQUEST=self.aq_acquire('REQUEST')

	    try:
		s=getattr(client, 'standard_error_message')
		v=HTML.__call__(s, client, REQUEST, error_type=error_type,
				error_value=error_value,
				error_tb=error_tb,error_traceback=error_tb,
				error_message=error_message)
	    except: v='Sorry, an error occured'
	    raise error_type, v, tb
	finally:
	    tb=None

    def uniqueId(self):
	return self._p_oid

    def aqObjectBind(self, ob):
	return ob.__of__(self)

    def manage(self, URL1):
        " "
        raise 'Redirect', "%s/manage_main" % URL1 

class Item_w__name__(Item):

    # Utility that returns the title if it is not blank and the id
    # otherwise.
    def title_or_id(self):
	return self.title or self.__name__

    # Utility that returns the title if it is not blank and the id
    # otherwise.  If the title is not blank, then the id is included
    # in parens.
    def title_and_id(self):
	t=self.title
	return t and ("%s (%s)" % (t,self.__name__)) or self.__name__

    def _setId(self, id):
	self.__name__=id

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
    result.append(join(traceback.format_exception_only(etype, value),
		       ' '))
#    sys.exc_type,sys.exc_value,sys.exc_traceback=etype,value,tb
    return result

def pretty_tb(t,v,tb):
    tb=format_exception(t,v,tb,200)
    tb=join(tb,'\n')
    return tb


############################################################################## 
#
# $Log: SimpleItem.py,v $
# Revision 1.22  1998/08/03 13:32:39  jim
# Made manage a redirect rather than an alias.
#
# Revision 1.21  1998/05/22 22:31:06  jim
# Moved some DB-related methods from ObjectManager and SimpleItem and stuffed them
# right into Persistent in Globals.
#
# Revision 1.20  1998/05/08 14:58:48  jim
# Changed permission settings to be in line with new machinery.
#
# Revision 1.19  1998/05/01 14:41:59  jeffrey
# added raise_standardErrorMessage logic
#
# Revision 1.18  1998/04/09 17:18:28  jim
# Added extra logic to verify session locks, which can become
# stale after a session undo.
#
# Revision 1.17  1998/03/18 17:55:36  brian
# Added uniqueId and aqObjectBind
#
# Revision 1.16  1998/03/09 19:58:21  jim
# changed session marking support
#
# Revision 1.15  1998/01/15 15:16:46  brian
# Fixed Setup, cleaned up SimpleItem
#
# Revision 1.14  1998/01/12 21:31:39  jim
# Made standard defaulr ['Manager', 'Shared'].
#
# Revision 1.13  1998/01/12 20:33:49  jim
# Made shared permission shared.
#
# Revision 1.12  1998/01/09 21:35:04  brian
# Security update
#
# Revision 1.11  1998/01/02 17:41:09  jim
# Factored old Management mix-in into Navigation and Tabs.
#
# Revision 1.10  1997/12/19 19:11:17  jim
# updated icon management strategy
#
# Revision 1.9  1997/12/18 16:45:42  jeffrey
# changeover to new ImageFile and HTMLFile handling
#
# Revision 1.8  1997/12/12 21:49:44  brian
# ui update
#
# Revision 1.7  1997/12/05 17:13:52  brian
# New UI
#
# Revision 1.6  1997/11/11 21:25:29  brian
# Added copy/paste support, restricted unpickling, fixed DraftFolder bug
#
# Revision 1.5  1997/11/11 19:26:09  jim
# Fixed bug in modified_in_session.
#
# Revision 1.4  1997/11/10 14:55:14  jim
# Added two new methods, bobobase_modification_time, and
# modified_in_session, to support flagging new and session objects.
#
# Revision 1.3  1997/11/06 18:41:56  jim
# Added manage_editedDialog.
#
# Revision 1.2  1997/10/30 19:51:09  jim
# Added methods to support tree browsing.
#
# Revision 1.1  1997/09/10 18:42:36  jim
# Added SimpleItem mix-in and new title/id methods.
#
#
