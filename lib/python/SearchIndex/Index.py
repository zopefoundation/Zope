############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved. 
#
############################################################################## 
__doc__='''Simple column indexes


$Id: Index.py,v 1.7 1997/09/17 18:58:08 brian Exp $'''
__version__='$Revision: 1.7 $'[11:-2]

from BTree import BTree
from intSet import intSet
import operator

ListType=type([])

class Index:
    """Index object interface"""

    def _init(self,data,schema,id):
	"""Create an index

	The arguments are:

	  'data' -- a mapping from integer object ids to objects or records,

	  'schema' -- a mapping from item name to index into data records.
              If 'data' is a mapping to objects, then schema should ne 'None'.

	  'id' -- the name of the item attribute to index.  This is either
	      an attribute name or a record key.
	"""
	self._data=data
	self._schema=schema
	self.id=id
	self._index=BTree()
	
	self._reindex()

    def clear(self):
	self._init()

    def _reindex(self,start=0):
	"""Recompute index data for data with ids >= start."""

	index=self._index
	
	if not start: index.clear()

	id=self.id
	if self._schema is None:
	    f=getattr
	else:
	    f=operator.__getitem__
	    id=self._schema[id]

	for i,row in self._data.items(start):
	    k=f(row,id)
	    try: set=index[k]
	    except KeyError:
		set=intSet()
		index[k]=set
	    set.insert(i)

    def index_item(self,i):
	"""Recompute index data for data with ids >= start."""

	index=self._index

	id=self.id
	if self._schema is None:
	    f=getattr
	else:
	    f=operator.__getitem__
	    id=self._schema[id]

	row=self._data[i]
	k=f(row,id)
	try: set=index[k]
	except KeyError:
	    set=intSet()
	    index[k]=set
	set.insert(i)

    def unindex_item(self,i):
	"""Recompute index data for data with ids >= start."""

	index=self._index

	id=self.id
	if self._schema is None:
	    f=getattr
	else:
	    f=operator.__getitem__
	    id=self._schema[id]

	row=self._data[i]
	k=f(row,id)
	try:
	    set=index[k]
	    set.remove(i)
	except KeyError: pass

    def _apply_index(self, request):
	"""Apply the index to query parameters given in the argument, request

	The argument should be a mapping object.

	If the request does not contain the needed parameters, then None is
	returned.

	Otherwise two objects are returned.  The first object is a
	ResultSet containing the record numbers of the matching
	records.  The second object is a tuple containing the names of
	all data fields used.

	"""
	id=self.id
	try: keys=request[id]
	except: return None

	if type(keys) is not ListType: keys=[keys]
	index=self._index
	r=None
	anyTrue=0
	for key in keys:
	    if key: anyTrue=1
	    try:
		set=index[key]
		if r is None: r=set
		else: r = r.union(set)
	    except KeyError: pass

	if r is None:
	    if anyTrue: r=intSet()
	    else: return None

	return r, (id,)
	

############################################################################## 
#
# $Log: Index.py,v $
# Revision 1.7  1997/09/17 18:58:08  brian
# Fixed a booboo in unindex_item
#
# Revision 1.6  1997/09/12 14:46:51  jim
# *** empty log message ***
#
# Revision 1.5  1997/09/12 14:18:04  jim
# Added logic to allow "blank" inputs.
#
# Revision 1.4  1997/09/10 21:46:18  jim
# Fixed bug that caused return of None when there were no matches.
#
# Revision 1.3  1997/09/10 17:25:26  jim
# Changed to use regular old BTree.
#
# Revision 1.2  1997/09/08 18:53:24  jim
# *** empty log message ***
#
# Revision 1.1  1997/09/08 18:52:04  jim
# *** empty log message ***
#
#
