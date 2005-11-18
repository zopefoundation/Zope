##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__='''Database Connection

$Id$'''
__version__='$Revision: 1.12 $'[11:-2]

from db import manage_DataSources
import Shared.DC.ZRDB.Connection, sys
from Globals import HTMLFile
from ExtensionClass import Base
import Acquisition

class Connection(Shared.DC.ZRDB.Connection.Connection):
    _isAnSQLConnection=1

    manage_options=Shared.DC.ZRDB.Connection.Connection.manage_options+(
        {'label': 'Browse', 'action':'manage_browse'},
        # {'label': 'Design', 'action':'manage_tables'},
        )

    manage_tables=HTMLFile('dtml/tables',globals())
    manage_browse=HTMLFile('dtml/browse',globals())

    info=None

    def tpValues(self):
        #if hasattr(self, '_v_tpValues'): return self._v_tpValues
        r=[]
        # self._v_tables=tables=TableBrowserCollection()
        #tables=tables.__dict__
        c=self._v_database_connection
        try:
            for d in c.tables(rdb=0):
                try:
                    name=d['TABLE_NAME']
                    b=TableBrowser()
                    b.__name__=name
                    b._d=d
                    b._c=c
                    # b._columns=c.columns(name)
                    try: b.icon=table_icons[d['TABLE_TYPE']]
                    except: pass
                    r.append(b)
                    # tables[name]=b
                except:
                    # print d['TABLE_NAME'], sys.exc_type, sys.exc_value
                    pass

        finally: pass #print sys.exc_type, sys.exc_value
        #self._v_tpValues=r
        return r

    def __getitem__(self, name):
        if name=='tableNamed':
            if not hasattr(self, '_v_tables'): self.tpValues()
            return self._v_tables.__of__(self)
        raise KeyError, name

    def manage_wizard(self, tables):
        " "

    def manage_join(self, tables, select_cols, join_cols, REQUEST=None):
        """Create an SQL join"""

    def manage_insert(self, table, cols, REQUEST=None):
        """Create an SQL insert"""

    def manage_update(self, table, keys, cols, REQUEST=None):
        """Create an SQL update"""

class TableBrowserCollection(Acquisition.Implicit):
    "Helper class for accessing tables via URLs"

class Browser(Base):
    def __getattr__(self, name):
        try: return self._d[name]
        except KeyError: raise AttributeError, name

class TableBrowser(Browser, Acquisition.Implicit):
    icon='what'
    Description=check=''
    info=HTMLFile('dtml/table_info',globals())
    menu=HTMLFile('dtml/table_menu',globals())

    def tpValues(self):
        r=[]
        tname=self.__name__
        for d in self._c.columns(tname):
            b=ColumnBrowser()
            b._d=d
            try: b.icon=field_icons[d['Type']]
            except: pass
            b.TABLE_NAME=tname
            r.append(b)
        return r

    def tpId(self): return self._d['TABLE_NAME']
    def tpURL(self): return "Table/%s" % self._d['TABLE_NAME']
    def Name(self): return self._d['TABLE_NAME']
    def Type(self): return self._d['TABLE_TYPE']

    manage_designInput=HTMLFile('dtml/designInput',globals())
    def manage_buildInput(self, id, source, default, REQUEST=None):
        "Create a database method for an input form"
        args=[]
        values=[]
        names=[]
        columns=self._columns
        for i in range(len(source)):
            s=source[i]
            if s=='Null': continue
            c=columns[i]
            d=default[i]
            t=c['Type']
            n=c['Name']
            names.append(n)
            if s=='Argument':
                values.append("<dtml-sql-value %s type=%s>'" %
                              (n, vartype(t)))
                a='%s%s' % (n, boboType(t))
                if d: a="%s=%s" % (a,d)
                args.append(a)
            elif s=='Property':
                values.append("<dtml-sql-value %s type=%s>'" %
                              (n, vartype(t)))
            else:
                if isStringType(t):
                    if find(d,"\'") >= 0: d=join(split(d,"\'"),"''")
                    values.append("'%s'" % d)
                elif d:
                    values.append(str(d))
                else:
                    raise ValueError, (
                        'no default was given for <em>%s</em>' % n)




class ColumnBrowser(Browser):
    icon='field'

    def check(self):
        return ('\t<input type=checkbox name="%s.%s">' %
                (self.TABLE_NAME, self._d['Name']))
    def tpId(self): return self._d['Name']
    def tpURL(self): return "Column/%s" % self._d['Name']
    def Description(self):
        d=self._d
        if d['Scale']:
            return " %(Type)s(%(Precision)s,%(Scale)s) %(Nullable)s" % d
        else:
            return " %(Type)s(%(Precision)s) %(Nullable)s" % d

table_icons={
    'TABLE': 'table',
    'VIEW':'view',
    'SYSTEM_TABLE': 'stable',
    }

field_icons={
    'BIGINT': 'int',
    'BINARY': 'bin',
    'BIT': 'bin',
    'CHAR': 'text',
    'DATE': 'date',
    'DECIMAL': 'float',
    'DOUBLE': 'float',
    'FLOAT': 'float',
    'INTEGER': 'int',
    'LONGVARBINARY': 'bin',
    'LONGVARCHAR': 'text',
    'NUMERIC': 'float',
    'REAL': 'float',
    'SMALLINT': 'int',
    'TIME': 'time',
    'TIMESTAMP': 'datetime',
    'TINYINT': 'int',
    'VARBINARY': 'bin',
    'VARCHAR': 'text',
    }
