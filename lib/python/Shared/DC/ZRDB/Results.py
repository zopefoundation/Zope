##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import ExtensionClass
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
            name=name.strip()
            if not name:
                raise ValueError, 'Empty column name, %s' % name
            if schema.has_key(name):
                raise ValueError, 'Duplicate column name, %s' % name
            schema[name]=i
            n=name.lower()
            if n != name: aliases.append((n, SQLAlias(name)))
            n=name.upper()
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
        for k, v in aliases:
            if not hasattr(r, k):
                setattr(r, k, v)

        if hasattr(brains, '__init__'):
            binit=brains.__init__
            if hasattr(binit,'im_func'): binit=binit.im_func
            def __init__(self, data, parent, binit=binit):
                Record.__init__(self,data)
                if parent is not None: self=self.__of__(parent)
                binit(self)

            setattr(r, '__init__', __init__)

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
        for i in indexes:
            item=items[i]
            t=item['type'].lower()
            if t=='s' or t=='t':
                t=='t'
                strings.append(i)
            else: nstrings.append(i)
            if item.has_key('width'): append('%s%s' % (item['width'], t))
            else: r.append(t)


        r=['\t'.join(self._names), '\t'.join(r)]
        append=r.append
        row=['']*len(items)
        tostr=str
        for d in self._data:
            for i in strings:
                v=tostr(d[i])
                if v:
                    if v.find('\\') > 0: v='\\\\'.join(v.split('\\'))
                    if v.find('\t') > 0: v='\\t'.join(v.split('\t'))
                    if v.find('\n') > 0: v='\\n'.join(v.split('\n'))
                row[i]=v
            for i in nstrings:
                row[i]=tostr(d[i])
            append('\t'.join(row))
        append('')

        return '\n'.join(r)
