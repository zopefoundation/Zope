#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''Class for reading RDB files


$Id: RDB.py,v 1.12 1998/01/16 21:43:47 jim Exp $'''
__version__='$Revision: 1.12 $'[11:-2]

import regex, regsub
from string import split, strip, lower, atof, atoi, atol, find
import DateTime
from Missing import MV
from array import array
from Record import Record
from Acquisition import Implicit

def parse_text(s):
    if find('\\') < 0 or (find('\\t') < 0 and find('\\n') < 0): return s
    r=[]
    for x in split(s,'\\\\'):
	x=join(split(x,'\\n'),'\n')
	r.append(join(split(x,'\\t'),'\t'))
    return join(r,'\\')


Parsers={'n': atof,
	 'i': atoi,
	 'l': atol,
	 'd': DateTime.DateTime,
	 't': parse_text,
	 }


record_classes={}

class NoBrains: pass

class DatabaseResults:
    """Class for reading RDB files
    """
    _index=None

    def __init__(self,file,brains=NoBrains, parent=None):

	self._file=file
	readline=file.readline
	line=readline()
	self._parent=parent

	comment_pattern=regex.compile('#')
	while line and comment_pattern.match(line) >= 0: line=readline()

	line=line[:-1]
	if line[-1:] in '\r\n': line=line[:-1]
	self._names=names=split(line,'\t')
	if not names: raise ValueError, 'No column names'

	self._schema=schema={}
	i=0
	for name in names:
	    name=strip(name)
	    if not name:
		raise ValueError, 'Empty column name, %s' % name
	    if schema.has_key(name):
		raise ValueError, 'Duplicate column name, %s' % name
	    schema[name]=i
	    i=i+1

	self._nv=nv=len(names)
	line=readline()
	line=line[:-1]
	if line[-1:] in '\r\n': line=line[:-1]
	
	self._defs=defs=split(line,'\t')
	if not defs: raise ValueError, 'No column definitions'
	if len(defs) != nv:
	    raise ValueError, (
		"""The number of column names and the number of column
		definitions are different.""")
	
	i=0
	self._parsers=parsers=[]
	defre=regex.compile('\([0-9]*\)\([a-zA-Z]\)?')
	self._data_dictionary=dd={}
	self.__items__=items=[]
	for _def in defs:
	    _def=strip(_def)
	    if not _def:
		raise ValueError, ('Empty column definition for %s' % names[i])
	    if defre.match(_def) < 0:
		raise ValueError, (
		    'Invalid column definition for, %s, for %s'
		    % _def, names[i])
	    type=lower(defre.group(2))
	    width=defre.group(1)
	    if width: width=atoi(width)
	    else: width=8

	    try: parser=Parsers[type]
	    except: parser=str

	    name=names[i]
	    d={'name': name, 'type': type, 'width': width, 'parser': parser}
	    items.append(d)
	    dd[name]=d
	    
	    parsers.append(i,parser)
	    i=i+1

	# Create a record class to hold the records.
	names=tuple(names)
	if record_classes.has_key((names,brains)):
	    r=record_classes[names,brains]
	else:
	    class r(Record, Implicit, brains):
		'Result record class'		    

	    r.__record_schema__=schema
	    for k in filter(lambda k: k[:2]=='__', Record.__dict__.keys()):
		setattr(r,k,getattr(Record,k))
		record_classes[names,brains]=r

	    if hasattr(brains, '__init__'):
		binit=brains.__init__
		if hasattr(binit,'im_func'): binit=binit.im_func
		def __init__(self, data, parent, binit=binit):
		    Record.__init__(self,data)
		    binit(self.__of__(parent))

		r.__dict__['__init__']=__init__
		    

	self._class=r

	# OK, we've read meta data, now get line indexes

	p=file.tell()
	save=self._lines=array('i')
	save=save.append
	l=readline()
	while l:
	    save(p)
	    p=p+len(l)
	    l=readline()

    def _searchable_result_columns(self): return self.__items__
    def names(self): return self._names
    def data_dictionary(self): return self._data_dictionary

    def __len__(self): return len(self._lines)

    def __getitem__(self,index):
	if index==self._index: return self._row
	file=self._file
	file.seek(self._lines[index])
	line=file.readline()
	line=line[:-1]
	if line and line[-1:] in '\r\n': line=line[:-1]
	fields=split(line,'\t')
	l=len(fields)
	nv=self._nv
	if l != nv:
	    if l < nv:
		fields=fields+['']*(nv-l)
	    else:
		raise ValueError, (
		    """The number of items in record %s is invalid
		    <pre>%s\n%s\n%s\n%s</pre>
		    """ 
		    % (index, ('='*40), line, ('='*40), fields))
        for i, parser in self._parsers:
            try: v=parser(fields[i])
            except:
                if fields[i]:
                    raise ValueError, (
                        """Invalid value, %s, for %s in record %s"""
                        % (fields[i], self._names[i], index))
                else: v=MV
            fields[i]=v

	fields=self._class(fields, self._parent)
	self._index=index
	self._row=fields
	return fields

File=DatabaseResults

############################################################################## 
#
# $Log: RDB.py,v $
# Revision 1.12  1998/01/16 21:43:47  jim
# Added parent to constructor so init can acquire
#
# Revision 1.11  1998/01/16 20:24:49  jim
# Added the abilility to define constructors in brains.
#
# Revision 1.10  1997/12/12 23:38:59  jim
# Added support for text (t) column type.
#
# Revision 1.9  1997/12/05 21:27:58  jim
# Better brain and record-as-instance support.
#
# Revision 1.8  1997/10/09 15:21:49  jim
# Fixed name error in exception handler.
#
# Revision 1.7  1997/10/09 15:11:12  jim
# Added optimization to cache result classes.
#
# Revision 1.6  1997/09/30 16:41:06  jim
# Fixed bug in handling empty lines.
#
# Revision 1.5  1997/09/26 22:17:37  jim
# more
#
# Revision 1.4  1997/09/25 18:40:58  jim
# new interfaces and RDB
#
# Revision 1.4  1997/09/18 17:43:10  jim
# Updated to use Missing.
#
# Revision 1.3  1997/09/12 18:37:11  jim
# Many changes leading to TextIndexes and many bug fixes.
#
# Revision 1.2  1997/09/02 21:24:06  jim
# *** empty log message ***
#
# Revision 1.1  1997/08/13 19:15:24  jim
# Converted name->id, description->title, copied from component
#
#
