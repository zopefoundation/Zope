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
__doc__='''Generic Database Connection Support

$Id$'''
__version__='$Revision: 1.39 $'[11:-2]

import Globals, OFS.SimpleItem, AccessControl.Role, Acquisition, sys
from DateTime import DateTime
from App.Dialogs import MessageDialog
from Globals import DTMLFile
from string import find, join, split
from Aqueduct import custom_default_report
from cStringIO import StringIO
from Results import Results
from sys import exc_info
from zLOG import LOG, ERROR
from cgi import escape
import DocumentTemplate, RDB
from zExceptions import BadRequest

class Connection(
    Globals.Persistent,
    AccessControl.Role.RoleManager,
    OFS.SimpleItem.Item,
    Acquisition.Implicit,
    ):

    # Specify definitions for tabs:
    manage_options=(
        (
        {'label':'Status', 'action':'manage_main'},
        {'label':'Properties', 'action':'manage_properties'},
        {'label':'Test', 'action':'manage_testForm'},
        )
        +AccessControl.Role.RoleManager.manage_options
        +OFS.SimpleItem.Item.manage_options
        )

    # Specify how individual operations add up to "permissions":
    __ac_permissions__=(
        ('View management screens', ('manage_main',)),
        ('Change Database Connections', ('manage_edit',)),
        ('Test Database Connections', ('manage_testForm','manage_test')),
        ('Open/Close Database Connection',
         ('manage_open_connection', 'manage_close_connection')),
        )

    _v_connected=''
    connection_string=''

    def __init__(self, id, title, connection_string, check=None):
        self.id=str(id)
        self.edit(title, connection_string, check)

    def __setstate__(self, state):
        Globals.Persistent.__setstate__(self, state)
        if self.connection_string:
            try: self.connect(self.connection_string)
            except:
                LOG('Shared.DC.ZRDB.Connection',
                    ERROR,
                    'Error connecting to relational database.',
                    error=exc_info())

    def title_and_id(self):
        s=Connection.inheritedAttribute('title_and_id')(self)
        if hasattr(self, '_v_connected') and self._v_connected:
            s="%s, which is connected" % s
        else:
            s="%s, which is <font color=red> not connected</font>" % s
        return s

    def title_or_id(self):
        s=Connection.inheritedAttribute('title_or_id')(self)
        if hasattr(self, '_v_connected') and self._v_connected:
            s="%s (connected)" % s
        else:
            s="%s (<font color=red> not connected</font>)" % s
        return s

    def connected(self): return self._v_connected

    def edit(self, title, connection_string, check=1):
        self.title=title
        self.connection_string=connection_string
        if check: self.connect(connection_string)

    manage_properties=DTMLFile('dtml/connectionEdit', globals())
    def manage_edit(self, title, connection_string, check=None, REQUEST=None):
        """Change connection
        """
        self.edit(title, connection_string, check)
        if REQUEST is not None:
            return MessageDialog(
                title='Edited',
                message='<strong>%s</strong> has been edited.' % escape(self.id),
                action ='./manage_main',
                )

    manage_testForm=DTMLFile('dtml/connectionTestForm', globals())
    def manage_test(self, query, REQUEST=None):
        "Executes the SQL in parameter 'query' and returns results"
        dbc=self()      #get our connection
        res=dbc.query(query)

        if type(res) is type(''):
            f=StringIO()
            f.write(res)
            f.seek(0)
            result=RDB.File(f)
        else:
            result=Results(res)

        if REQUEST is None:
            return result       #return unadulterated result objects

        if result._searchable_result_columns():
            r=custom_default_report(self.id, result)
        else:
            r='This statement returned no results.'

        report=DocumentTemplate.HTML(
            '<html><body bgcolor="#ffffff" link="#000099" vlink="#555555">\n'
            '<dtml-var name="manage_tabs">\n<hr>\n%s\n\n'
            '<hr><h4>SQL Used:</strong><br>\n<pre>\n%s\n</pre>\n<hr>\n'
            '</body></html>'
            % (r, query))

        report=apply(report,(self,REQUEST),{self.id:result})

        return report


    manage_main=DTMLFile('dtml/connectionStatus', globals())

    def manage_close_connection(self, REQUEST=None):
        " "
        try: 
            if hasattr(self,'_v_database_connection'):
                self._v_database_connection.close()
        except:
            LOG('Shared.DC.ZRDB.Connection',
                ERROR,
                'Error closing relational database connection.',
                error=exc_info())
        self._v_connected=''
        if REQUEST is not None:
            return self.manage_main(self, REQUEST)

    def manage_open_connection(self, REQUEST=None):
        " "
        self.connect(self.connection_string)
        return self.manage_main(self, REQUEST)

    def __call__(self, v=None):
        try: return self._v_database_connection
        except AttributeError:
            s=self.connection_string
            if s:
                self.connect(s)
                return self._v_database_connection
            raise BadRequest,(
                '''The database connection is not connected''')

    def connect(self,s):
        self.manage_close_connection()
        DB=self.factory()
        try:
            try:
                self._v_database_connection=DB(s)
            except:
                t, v, tb = sys.exc_info()
                raise BadRequest, (
                    '<strong>Invalid connection string: </strong><CODE>%s</CODE><br>\n'
                    '<!--\n%s\n%s\n-->\n'
                    % (s,t,v)), tb
        finally: tb=None
        self._v_connected=DateTime()

        return self

    def sql_quote__(self, v):
        if find(v,"\'") >= 0: v=join(split(v,"\'"),"''")
        return "'%s'" % v
