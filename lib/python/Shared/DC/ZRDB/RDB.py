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
__doc__='''Class for reading RDB files


$Id: RDB.py,v 1.23 1999/03/10 00:15:44 klm Exp $'''
__version__='$Revision: 1.23 $'[11:-2]

import regex, regsub
from string import split, strip, lower, upper, atof, atoi, atol, find, join
import DateTime
from Missing import MV
from array import array
from Record import Record
from Acquisition import Implicit
import ExtensionClass

def parse_text(s):
    if find(s,'\\') < 0 and (find(s,'\\t') < 0 and find(s,'\\n') < 0): return s
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

class SQLAlias(ExtensionClass.Base):
    def __init__(self, name): self._n=name
    def __of__(self, parent): return getattr(parent, self._n)
 
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
        if line and line[-1:] in '\r\n': line=line[:-1]
        self._names=names=split(line,'\t')
        if not names: raise ValueError, 'No column names'

        aliases=[]
        self._schema=schema={}
        i=0
        for name in names:
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

            # Add SQL Aliases
            d=r.__dict__
            for k, v in aliases:
                if not hasattr(r,k): d[k]=v

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

        parent=self._parent
        fields=self._class(fields, parent)
        self._index=index
        self._row=fields
        if parent is None: return fields
        return fields.__of__(parent)

File=DatabaseResults
