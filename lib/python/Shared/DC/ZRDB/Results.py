##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import ExtensionClass
import string
from string import strip, lower, upper, join
from Acquisition import Implicit
from Record import Record

class SQLAlias(ExtensionClass.Base):
    def __init__(self, name): self._n=name
    def __of__(self, parent): return getattr(parent, self._n)

class NoBrains: pass

class Results:
    """Class for providing a nice interface to DBI result data
    """
    _index=None

    # We need to allow access to not-explicitly-protected
    # individual record objects contained in the result.
    __allow_access_to_unprotected_subobjects__=1

    def __init__(self,(items,data),brains=NoBrains, parent=None,
                 zbrains=None):

        self._data=data
        self.__items__=items
        self._parent=parent
        self._names=names=[]
        self._schema=schema={}
        self._data_dictionary=dd={}
        aliases=[]
        if zbrains is None: zbrains=NoBrains
        i=0
        for item in items:
            name=item['name']
            name=strip(name)
            if not name:
                raise ValueError, 'Empty column name, %s' % name
            if schema.has_key(name):
                raise ValueError, 'Duplicate column name, %s' % name
            schema[name]=i
            n=lower(name)
            if n != name: aliases.append((n, SQLAlias(name)))
            n=upper(name)
            if n != name: aliases.append((n, SQLAlias(name)))
            dd[name]=item
            names.append(name)
            i=i+1

        self._nv=nv=len(names)

        # Create a record class to hold the records.
        names=tuple(names)

        class r(Record, Implicit, brains, zbrains):
            'Result record class'

        r.__record_schema__=schema
        for k in Record.__dict__.keys():
            if k[:2]=='__':
                setattr(r,k,getattr(Record,k))

        # Add SQL Aliases
        d=r.__dict__
        for k, v in aliases:
            if not hasattr(r,k): d[k]=v

        if hasattr(brains, '__init__'):
            binit=brains.__init__
            if hasattr(binit,'im_func'): binit=binit.im_func
            def __init__(self, data, parent, binit=binit):
                Record.__init__(self,data)
                if parent is not None: self=self.__of__(parent)
                binit(self)

            r.__dict__['__init__']=__init__

        self._class=r

        # OK, we've read meta data, now get line indexes

    def _searchable_result_columns(self): return self.__items__
    def names(self): return self._names
    def data_dictionary(self): return self._data_dictionary

    def __len__(self): return len(self._data)

    def __getitem__(self,index):
        if index==self._index: return self._row
        parent=self._parent
        fields=self._class(self._data[index], parent)
        if parent is not None: fields=fields.__of__(parent)
        self._index=index
        self._row=fields
        return fields

    def tuples(self):
        return map(tuple, self)

    def dictionaries(self):
        r=[]
        a=r.append
        names=self.names()
        for row in self:
            d={}
            for n in names: d[n]=row[n]
            a(d)

        return r

    def asRDB(self): # Waaaaa
        r=[]
        append=r.append
        strings=[]
        nstrings=[]
        items=self.__items__
        indexes=range(len(items))
        join=string.join
        for i in indexes:
            item=items[i]
            t=lower(item['type'])
            if t=='s' or t=='t':
                t=='t'
                strings.append(i)
            else: nstrings.append(i)
            if item.has_key('width'): append('%s%s' % (item['width'], t))
            else: r.append(t)


        r=[join(self._names, '\t'), join(r,'\t')]
        append=r.append
        find=string.find
        split=string.split
        row=['']*len(items)
        tostr=str
        for d in self._data:
            for i in strings:
                v=tostr(d[i])
                if v:
                    if find(v,'\\') > 0: v=join(split(v,'\\'),'\\\\')
                    if find(v,'\t') > 0: v=join(split(v,'\t'),'\\t')
                    if find(v,'\n') > 0: v=join(split(v,'\n'),'\\n')
                row[i]=v
            for i in nstrings:
                row[i]=tostr(d[i])
            append(join(row,'\t'))
        append('')

        return join(r,'\n')
