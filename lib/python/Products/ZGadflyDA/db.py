##############################################################################
#
# Zope Public License (ZPL) Version 0.9.5
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
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
# 3. Any use, including use of the Zope software to operate a website,
#    must either comply with the terms described below under
#    "Attribution" or alternatively secure a separate license from
#    Digital Creations.  Digital Creations will not unreasonably
#    deny such a separate license in the event that the request
#    explains in detail a valid reason for withholding attribution.
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
# Attribution
# 
#   Individuals or organizations using this software as a web site must
#   provide attribution by placing the accompanying "button" and a link
#   to the accompanying "credits page" on the website's main entry
#   point.  In cases where this placement of attribution is not
#   feasible, a separate arrangment must be concluded with Digital
#   Creations.  Those using the software for purposes other than web
#   sites must provide a corresponding attribution in locations that
#   include a copyright using a manner best suited to the application
#   environment.  Where attribution is not possible, or is considered
#   to be onerous for some other reason, a request should be made to
#   Digital Creations to waive this requirement in writing.  As stated
#   above, for valid requests, Digital Creations will not unreasonably
#   deny such requests.
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

'''$Id: db.py,v 1.4 1998/12/16 15:28:47 jim Exp $'''
__version__='$Revision: 1.4 $'[11:-2]

import string, sys, os
from string import strip, split, find, join
from gadfly import gadfly
import Globals

data_dir=os.path.join(Globals.data_dir,'gadfly')

def manage_DataSources():
    
    if not os.path.exists(data_dir):
        try:
            os.mkdir(data_dir)
            os.mkdir(os.path.join(data_dir,'demo'))
        except:
            raise 'Gadfly Error', (
                """
                The Zope Gadfly Database Adapter requires the
                existence of the directory, <code>%s</code>.  An error
                occurred  while trying to create this directory.
                """ % data_dir)
    if not os.path.isdir(data_dir):
        raise 'Gadfly Error', (
            """
            The Zope Gadfly Database Adapter requires the
            existence of the directory, <code>%s</code>.  This
            exists, but is not a directory.
            """ % data_dir)
    
    return map(
        lambda d: (d,''),
        filter(lambda f, i=os.path.isdir, d=data_dir, j=os.path.join:
               i(j(d,f)),
               os.listdir(data_dir))
        )

class DB:

    database_error=gadfly.error

    def tables(self,*args,**kw):
        return map(lambda name: {
            'TABLE_NAME': name,
            'TABLE_TYPE': 'TABLE',
            }, self.db.table_names())

    def columns(self, table_name):
        return map(lambda col: {
            'Name': col.colid, 'Type': col.datatype, 'Precision': 0,
            'Scale': 0, 'Nullable': 'with Null'
            }, self.db.database.datadefs[table_name].colelts)

    def __init__(self,connection):
        path=os.path
        dir=path.join(data_dir,connection)
        if not path.isdir(dir):
            raise self.database_error, 'invalid database error, ' + connection

        if not path.exists(path.join(dir,connection+".gfd")):
            db=gadfly.gadfly()
            db.startup(connection,dir)
        else: db=gadfly.gadfly(connection,dir)

        self.connection=connection
        self.db=db
        self.cursor=db.cursor()

    def query(self,query_string, max_rows=9999999):
        self._register()
        c=self.db.cursor()
        queries=filter(None, map(strip,split(query_string, '\0')))
        if not queries: raise 'Query Error', 'empty query'
        names=None
        result='cool\ns\n'
        for qs in queries:
            c.execute(qs)
            d=c.description
            if d is None: continue
            if names is not None:
                raise 'Query Error', (
                    'select in multiple sql-statement query'
                    )
            names=map(lambda d: d[0], d)
            results=c.fetchmany(max_rows)
            nv=len(names)
            indexes=range(nv)
            row=['']*nv
            defs=[maybe_int]*nv
            j=join
            rdb=[j(names,'\t'),None]
            append=rdb.append
            for result in results:
                for i in indexes:
                    try: row[i]=defs[i](result[i])
                    except NewType, v: row[i], defs[i] = v
                append(j(row,'\t'))
            rdb[1]=j(map(lambda d, Defs=Defs: Defs[d], defs),'\t')
            rdb.append('')
            result=j(rdb,'\n')

        return result

    class _p_jar:
        # This is place holder for new transaction machinery 2pc
        def __init__(self, db=None): self.db=db
        def begin_commit(self, *args): pass
        def finish_commit(self, *args): pass

    _p_jar=_p_jar(_p_jar())

    _p_oid=_p_changed=_registered=None
    def _register(self):
        if not self._registered:
            try:
                get_transaction().register(self)
                self._registered=1
            except: pass

    def __inform_commit__(self, *ignored):
        self.db.commit()
        self._registered=0

    def __inform_abort__(self, *ignored):
        self.db.rollback()
        self.db.checkpoint()
        self._registered=0


NewType="Excecption to raise when sniffing types, blech"
def maybe_int(v, int_type=type(0), float_type=type(0.0), t=type):
    t=t(v)
    if t is int_type: return str(v)
    if v is None or v=='': return ''
    if t is float_type: raise NewType, (maybe_float(v), maybe_float)

    raise NewType, (maybe_string(v), maybe_string)

def maybe_float(v, int_type=type(0), float_type=type(0.0), t=type):
    t=t(v)
    if t is int_type or t is float_type: return str(v)
    if v is None or v=='': return ''

    raise NewType, (maybe_string(v), maybe_string)

def maybe_string(v):
    v=str(v)
    if find(v,'\t') >= 0 or find(v,'\t'):
        raise NewType, (must_be_text(v), must_be_text)
    return v

def must_be_text(v, f=find, j=join, s=split):
    if f(v,'\\'):
        v=j(s(v,'\\'),'\\\\')
        v=j(s(v,'\t'),'\\t')
        v=j(s(v,'\n'),'\\n')
    return v

Defs={maybe_int: 'i', maybe_float:'n', maybe_string:'s', must_be_text:'t'}
