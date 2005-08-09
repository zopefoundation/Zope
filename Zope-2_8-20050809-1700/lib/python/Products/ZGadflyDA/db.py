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

'''$Id$'''
__version__='$Revision: 1.14 $'[11:-2]

import os
from string import strip, split
import gadfly
import Globals, Shared.DC.ZRDB.THUNK
from DateTime import DateTime

data_dir=os.path.join(Globals.data_dir,'gadfly')

from Products.ZGadflyDA import GadflyError, QueryError

def manage_DataSources():

    if not os.path.exists(data_dir):
        try:
            os.mkdir(data_dir)
            os.mkdir(os.path.join(data_dir,'demo'))
        except:
            raise GadflyError, (
                """
                The Zope Gadfly Database Adapter requires the
                existence of the directory, <code>%s</code>.  An error
                occurred  while trying to create this directory.
                """ % data_dir)
    if not os.path.isdir(data_dir):
        raise GadflyError, (
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

class DB(Shared.DC.ZRDB.THUNK.THUNKED_TM):

    database_error=gadfly.error
    opened=''

    def tables(self,*args,**kw):
        if self.db is None: self.open()
        return map(
            lambda name: {
            'TABLE_NAME': name,
            'TABLE_TYPE': 'TABLE',
            },
            filter(self.db.database.datadefs.has_key, self.db.table_names())
            )

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
        if not queries: raise QueryError, 'empty query'
        desc=None
        result=[]
        for qs in queries:
            c.execute(qs)
            d=c.description
            if d is None: continue
            if desc is None: desc=d
            elif d != desc:
                raise QueryError, (
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

    # Gadfly needs the extra checkpoint call.
    def _abort(self):
        self.db.rollback()
        self.db.checkpoint()
