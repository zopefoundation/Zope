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
database_type='Gadfly'
__doc__='''%s Database Connection

$Id: DA.py,v 1.12 2001/01/08 22:47:03 brian Exp $''' % database_type
__version__='$Revision: 1.12 $'[11:-2]

from db import DB, manage_DataSources
import sys, DABase, Globals
import Shared.DC.ZRDB.Connection, ThreadLock
_Connection=Shared.DC.ZRDB.Connection.Connection

_connections={}
_connections_lock=ThreadLock.allocate_lock()

data_sources=manage_DataSources

addConnectionForm=Globals.HTMLFile('dtml/connectionAdd',globals())
def manage_addZGadflyConnection(
    self, id, title, connection, check=None, REQUEST=None):
    """Add a DB connection to a folder"""

    # Note - type checking is taken care of by _setObject 
    # and the Connection object constructor.
    self._setObject(id, Connection(
        id, title, connection, check))
    if REQUEST is not None: return self.manage_main(self,REQUEST)
    return self.manage_main(self,REQUEST)       

class Connection(DABase.Connection):
    " "
    database_type=database_type
    id='%s_database_connection' % database_type
    meta_type=title='Z %s Database Connection' % database_type
    icon='misc_/Z%sDA/conn' % database_type

    manage_properties=Globals.HTMLFile('dtml/connectionEdit', globals(),
                                       data_sources=data_sources)

    def connected(self):
        if hasattr(self, '_v_database_connection'):
            return self._v_database_connection.opened
        return ''
    
    def title_and_id(self):
        s=_Connection.inheritedAttribute('title_and_id')(self)
        if (hasattr(self, '_v_database_connection') and
            self._v_database_connection.opened):
            s="%s, which is connected" % s
        else: 
            s="%s, which is <font color=red> not connected</font>" % s
        return s

    def title_or_id(self):
        s=_Connection.inheritedAttribute('title_and_id')(self)
        if (hasattr(self, '_v_database_connection') and
            self._v_database_connection.opened):
            s="%s (connected)" % s
        else: 
            s="%s (<font color=red> not connected</font>)" % s
        return s

    def connect(self,s):
        _connections_lock.acquire()
        try:
            c=_connections
            if c.has_key(s):
                c=self._v_database_connection=c[s]
                if not c.opened: c.open()
                return self
    
            try:
                try:
                    self._v_database_connection=c[s]=DB(s)
                except:
                    t, v, tb = sys.exc_info()
                    raise 'BadRequest', (
                        '<strong>Invalid connection string: </strong>'
                        '<CODE>%s</CODE><br>\n'
                        '<!--\n%s\n%s\n-->\n'
                        % (s,t,v)), tb
            finally: tb=None
    
            return self
        finally:
            _connections_lock.release()

