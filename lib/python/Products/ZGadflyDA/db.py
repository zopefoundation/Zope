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

'''$Id: db.py,v 1.5 1998/12/17 18:48:36 jim Exp $'''
__version__='$Revision: 1.5 $'[11:-2]

import os
from string import strip, split
from gadfly import gadfly
import Globals
from DateTime import DateTime

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
    opened=''

    def tables(self,*args,**kw):
        if self.db is None: self.open()
        return map(lambda name: {
            'TABLE_NAME': name,
            'TABLE_TYPE': 'TABLE',
            }, self.db.table_names())

    def columns(self, table_name):
        if self.db is None: self.open()
        return map(lambda col: {
            'Name': col.colid, 'Type': col.datatype, 'Precision': 0,
            'Scale': 0, 'Nullable': 'with Null'
            }, self.db.database.datadefs[table_name].colelts)

    def open(self):
        connection=self.connection
        path=os.path
        dir=path.join(data_dir,connection)
        if not path.isdir(dir):
            raise self.database_error, 'invalid database error, ' + connection

        if not path.exists(path.join(dir,connection+".gfd")):
            db=gadfly.gadfly()
            db.startup(connection,dir)
        else: db=gadfly.gadfly(connection,dir)
        self.db=db
        self.opened=DateTime()

    def close(self):
        self.db=None
        del self.opened

    def __init__(self,connection):
        self.connection=connection
        self.open()

    def query(self,query_string, max_rows=9999999):
        if self.db is None: self.open()
        self._register()
        c=self.db.cursor()
        queries=filter(None, map(strip,split(query_string, '\0')))
        if not queries: raise 'Query Error', 'empty query'
        desc=None
        result=[]
        for qs in queries:
            c.execute(qs)
            d=c.description
            if d is None: continue
            if desc is None: desc=d
            elif d != desc:
                raise 'Query Error', (
                    'Multiple incompatible selects in '
                    'multiple sql-statement query'
                    )
            
            if not result: result=c.fetchmany(max_rows)
            elif len(result) < max_rows:
                result=result+c.fetchmany(max_rows-len(result))

        if desc is None: return (),()

        items=[]
        for name, type, width, ds, p, scale, null_ok in desc:
            if type=='NUMBER':
                if scale==0: type='i'
                else: type='n'
            elif type=='DATE':
                type='d'
            else: type='s'
            items.append({
                'name': name,
                'type': type,
                'width': width,
                'null': null_ok,
                })
        return items, result

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
