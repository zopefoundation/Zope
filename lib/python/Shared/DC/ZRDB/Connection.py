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
__doc__='''Generic Database Connection Support


$Id: Connection.py,v 1.16 1998/12/16 15:25:48 jim Exp $'''
__version__='$Revision: 1.16 $'[11:-2]

import Globals, OFS.SimpleItem, AccessControl.Role, Acquisition, sys
from DateTime import DateTime
from App.Dialogs import MessageDialog
from Globals import HTMLFile
from string import find, join, split

class Connection(
    Globals.Persistent,
    AccessControl.Role.RoleManager,
    OFS.SimpleItem.Item,
    Acquisition.Implicit,
    ):    

    # Specify definitions for tabs:
    manage_options=(
        {'label':'Status', 'action':'manage_main'},
        {'label':'Properties', 'action':'manage_properties'},
        {'label':'Security',   'action':'manage_access'},
        )
 
    # Specify how individual operations add up to "permissions":
    __ac_permissions__=(
        ('View management screens', ('manage_tabs','manage_main',
                                     'manage_properties')),
        ('Change permissions',      ('manage_access',)            ),
        ('Change Database Connections', ('manage_edit',)              ),
        ('Open/Close Database Connection',
         ('manage_open_connection',
          'manage_close_connection')),
        )

    _v_connected=''
    connection_string=''

    def __init__(self, id, title, connection_string, check=None):
        self.id=id
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
        self.edit(title, connection_string, check)
        if REQUEST is not None:
            return MessageDialog(
                title='Edited',
                message='<strong>%s</strong> has been edited.' % self.id,
                action ='./manage_main',
                )


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
                t, v, tb = sys.exc_type, sys.exc_value, sys.exc_traceback
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
