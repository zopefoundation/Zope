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
__doc__='''Simple RDB data-file reader


$Id: RDB.py,v 1.3 1997/08/07 13:58:07 jim Exp $'''
__version__='$Revision: 1.3 $'[11:-2]

import regex, regsub
from string import split, strip, lower, atof, atoi, atol

Parsers={'n': atof,
	 'i': atoi,
	 'l': atol,
	 }

try:
    import DateTime
    Parsers['d']=DateTime.DateTime
except: pass



class Record:

    def __init__(self, data, schema, names):
	'''Create a record with data'''
	self._r_data=data
	self._r_schema=schema
	self._r_names=names

    def __len__(self):
	'''Return the record length'''
	return len(self._r_data)

    def __getattr__(self,name):
	'''Get the value of the column with name, \'name\' '''
	return self._r_data[self._r_schema[name]]

    def __getitem__(self,key):
	'''Get a value by key

	The key may be either an integer column index or a string
	column name.
	'''
	data=self._r_data
	if type(key) is type(0): return data[key]
	else:                    return self._r_data[self._r_schema[key]]

    def update(self, *args, **name_value_pairs):
	'''Update a record

	The update method supports a number of syntaxes:

	Multiple positional arguments --
	  In this case, the number of positional arguments must equal
	  the number of columns in the record.

	A single positional argument with optional keyword parameters --
	  The single argument may be a list, a tuple, or a mapping
	  object.

	  If the argument is a list or a tuple, its length must be
	  equal to the length of the record.  The items in the record
	  are replaced by the values in the argument.

	  If the argument is a mapping object, it must have a 'keys'
	  method that returns a sequence of keys.  For those keys that
	  are record item names, the corresponding values are used to
	  update the record items.  The argument may have keys that
	  are not item names, and it need not have keys for all item
	  names.

	  If keyword parameters are provided, they will be used to
	  update items in the record.  All keyword names must match
	  item names, although keyword arguments need not be provided
	  for all items.

	Keyword arguments with no positional arguments--
	  The keyword arguments are used to update items in the
	  record.  All keyword names must match item names, although
	  keyword arguments need not be provided for all items.

	For example, if a record, 'r' has items 'col1', 'col2', and 'col2',
	then the following expressions are equivalent::

	  r.update('spam',1,2)

	  r.update({'col1':'spam', 'col3':2, 'col2': 1})

	  r.update(col2=1, col1='spam', col3=2)

	Note that because records are mapping objects, one record can be
	used to update another, even if the records have different schema.
	'''
	data=self._r_data
	schema=self._r_schema
	l=len(data)
	la=len(args)
	if la > 1:
	    if la != l: raise TypeError, (
		'number of arguments does not match record length')
	    data[:]=list(args)
	elif la==1:
	    args=args[0]
	    if type(args) is type(()) or type(args) is type([]):
		if len(args) != l: raise TypeError, (
		'number of arguments does not match record length')
		data[:]=list(args)
	    else:
		for k in args.keys():
		    try: data[schema[k]]=args[k]
		    except KeyError: pass

	for k in name_value_pairs.keys():
	    data[schema[k]]=name_value_pairs[k]
	
    def keys(self):
	'''Return the item names in item order'''
	# In this implementation, our class has this information handy
	return self._r_item_names

    def values(self):
	'''Return our data values, in item order'''
	return self._r_data[:]
	
    def items(self):
	'''Return a sequence of item name and item pairs

	The sequence is returned in item order.'''
	return map(None, self._r_names, self._r_data)

    def has_key(self,key):
	'''Return whether the given key is an item name'''
	return self._schema.has_key(key)

class RDB:
    """Class for reading RDB files
    """

    def __init__(self,file,RecordClass=Record):

	self._file=file
	line=file.readline()
	self._record_positions=[]
	self._Record=RecordClass

	comment_pattern=regex.compile('#')
	while line and comment_pattern.match(line) >= 0: line=file.readline()

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
	line=file.readline()
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
	self.__items__=__items__=[]
	defre=regex.compile('\([0-9]*\)\([a-zA-Z]\)?[^\0- ]*[\0- ]*\(.+\)')
	for _def in defs:
	    _def=strip(_def)
	    if not _def:
		raise ValueError, ('Empty column definition for %s' % names[i])
	    if defre.match(_def) < 0:
		raise ValueError, (
		    'Invalid column definition for, %s, for %s'
		    % _def, names[i])
	    width, type, remark = defre.group(1,2,3)
	    try: width=atoi(width)
	    except: width=8
	    type=lower(type)
	    
	    try: parsers.append(i,Parsers[type])
	    except: pass
	    __items__.append({'type':type, 'width': width, 'name': names[i],
			      'remark':remark})
	    i=i+1
	
	self._index=-1
	self._pos=file.tell()

    def names(self): return self._names

    def parse(self, line, _index=-1):
	line=line[:-1]
        while line[-1:] in '\r\n': line=line[:-1]
        fields=split(line,'\t')
        if len(fields) != self._nv: raise ValueError, (
            """The number of items in record %s is invalid
            <pre>%s\n%s\n%s\n%s</pre>
            """ 
            % (_index, ('='*40), line, ('='*40), fields))
        for i, parser in self._parsers:
            try: v=parser(fields[i])
            except:
                if fields[i]:
                    raise ValueError, (
                        """Invalid value, %s, for %s in record %s"""
                        % (fields[i], self._names[i], _index))
                else: v=None
            fields[i]=v
	return fields

    def __len__(self):
	_index=self._index
        try: pos=self._pos
        except: return _index+1
        file=self._file
        readline=file.readline
        tell=file.tell
        if pos != tell(): file.seek(pos)
        save_position=self._record_positions.append
        while 1:
            line=readline()
            if not line:
                del self._pos
		self._index=_index
                return _index+1
            _index=_index+1
            save_position(pos)
            pos=tell()

    def __getitem__(self,input_index):
	index=input_index
	if index < 0:
	    index=len(self)-index
	    if index < 0: raise IndexError, input_index
	_index=self._index
	if index==_index:
	    try: return self._row
	    except: pass

	if index > _index:
	    try: pos=self._pos
	    except: raise IndexError, input_index
	    file=self._file
	    readline=file.readline
	    tell=file.tell
	    if pos != tell(): file.seek(pos)
	    save_position=self._record_positions.append
	    while index > _index:
		line=readline()
		if not line:
		    del self._pos
		    self._index=_index
		    raise IndexError, input_index
		_index=_index+1
		save_position(pos)
		pos=tell()
		if index == _index:
		    self._pos=pos
		    self._index=_index
		    self._row=line=self._Record(
			self.parse(line,_index), self._schema, self._names)
		    return line

	else:
	    file=self._file
	    file.seek(self._record_positions[index])
	    return self._Record(
		self.parse(file.readline(), index), self._schema, self._names)

	raise IndexError, input_index
	

class rdb:

    def __init__(self, file):
	self._file=file

	


############################################################################## 
# Test functions:
#

def main():
    # The "main" program for this module
    import sys
    print sys.argv[0]+" is a pure module and doesn't do anything by itself."


if __name__ == "__main__": main()

############################################################################## 
#
# $Log: RDB.py,v $
# Revision 1.3  1997/08/07 13:58:07  jim
# Fixed bug in date-time handling.
#
# Revision 1.2  1997/07/28 21:30:13  jim
# Fixed bug in handling errors.
#
# Revision 1.1  1997/07/25 16:07:19  jim
# initial
#
#
