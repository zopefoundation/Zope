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
__doc__='''Generic Database Connection Support

$Id: Connection.py,v 1.26 2000/07/26 15:44:05 brian Exp $'''
__version__='$Revision: 1.26 $'[11:-2]

import Globals, OFS.SimpleItem, AccessControl.Role, Acquisition, sys
from DateTime import DateTime
from App.Dialogs import MessageDialog
from Globals import HTMLFile
from string import find, join, split
from Aqueduct import custom_default_report
from Results import Results
import DocumentTemplate

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
            except: pass

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
    
    manage_properties=HTMLFile('connectionEdit', globals())
    def manage_edit(self, title, connection_string, check=None, REQUEST=None):
        """Change connection
        """
        title=str(title)
        connection_string=str(connection_string)
        self.edit(title, connection_string, check)
        if REQUEST is not None:
            return MessageDialog(
                title='Edited',
                message='<strong>%s</strong> has been edited.' % self.id,
                action ='./manage_main',
                )

    manage_testForm=HTMLFile('connectionTestForm', globals())
    def manage_test(self, query, REQUEST=None):
        "Executes the SQL in parameter 'query' and returns results"
        dbc=self()      #get our connection
        res=dbc.query(query)
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
                

    manage_main=HTMLFile('connectionStatus', globals())

    def manage_close_connection(self, REQUEST):
        " "
        try: self._v_database_connection.close()
        except: pass
        self._v_connected=''
        return self.manage_main(self, REQUEST)

    def manage_open_connection(self, REQUEST=None):
        " "
        self.connect(self.connection_string)
        return self.manage_main(self, REQUEST)

    def __call__(self, v=None):
        try: return self._v_database_connection
        except AttributeError:
            s=self.connection_string
            if s: return self.connect(s)
            raise 'Database Not Connected',(
                '''The database connection is not connected''')

    def connect(self,s):
        try: self._v_database_connection.close()
        except: pass
        self._v_connected=''
        DB=self.factory()
        try:
            try:
                self._v_database_connection=DB(s)
            except:
                t, v, tb = sys.exc_info()
                raise 'BadRequest', (
                    '<strong>Invalid connection string: </strong><CODE>%s</CODE><br>\n'
                    '<!--\n%s\n%s\n-->\n'
                    % (s,t,v)), tb
        finally: tb=None
        self._v_connected=DateTime()

        return self

    def sql_quote__(self, v):
        if find(v,"\'") >= 0: v=join(split(v,"\'"),"''")
        return "'%s'" % v
