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
__doc__='''SQL Methods


$Id: SQL.py,v 1.19 2001/06/07 22:18:45 shane Exp $'''
__version__='$Revision: 1.19 $'[11:-2]

import Shared.DC.ZRDB.DA
from Globals import DTMLFile
from webdav.WriteLockInterface import WriteLockInterface

def SQLConnectionIDs(self):
    """Find SQL database connections in the current folder and above

    This function return a list of ids.
    """
    ids={}
    have_id=ids.has_key
    StringType=type('')

    while self is not None:
        if hasattr(self, 'objectValues'):
            for o in self.objectValues():
                if (hasattr(o,'_isAnSQLConnection') and o._isAnSQLConnection
                    and hasattr(o,'id')):
                    id=o.id
                    if type(id) is not StringType: id=id()
                    if not have_id(id):
                        if hasattr(o,'title_and_id'): o=o.title_and_id()
                        else: o=id
                        ids[id]=id
        if hasattr(self, 'aq_parent'): self=self.aq_parent
        else: self=None

    ids=map(lambda item: (item[1], item[0]), ids.items())
    ids.sort()
    return ids

manage_addZSQLMethodForm=DTMLFile('dtml/add', globals())
def manage_addZSQLMethod(self, id, title,
                                connection_id, arguments, template,
                                REQUEST=None, submit=None):
    """Add an SQL Method

    The 'connection_id' argument is the id of a database connection
    that resides in the current folder or in a folder above the
    current folder.  The database should understand SQL.

    The 'arguments' argument is a string containing an arguments
    specification, as would be given in the SQL method cration form.

    The 'template' argument is a string containing the source for the
    SQL Template.
    """

    # Note - type checking is handled by _setObject and constructor.
    self._setObject(id, SQL(id, title, connection_id, arguments, template))
    if REQUEST is not None:
        try: u=self.DestinationURL()
        except: u=REQUEST['URL1']
        if submit==" Add and Edit ":
            u="%s/%s/manage_main" % (u,id)
        elif submit==" Add and Test ":
            u="%s/%s/manage_testForm" % (u,id)
        else:
            u=u+'/manage_main'
            
        REQUEST.RESPONSE.redirect(u)
    return ''

class SQL(Shared.DC.ZRDB.DA.DA):
    """SQL Database methods

    SQL Database methods are used to access external SQL databases.

    They support three important abstractions:

      - Method

        SQL Methods behave like methods of the folders they are
        accessed in.  In particular, they can be used from other
        methods, like Documents, ExternalMethods, and even other SQL
        Methods.

      - Searchability

        Database methods support the Searchable Object Interface.
        Search interface wizards can be used to build user
        interfaces to them.  They can be used in joins and
        unions. They provide meta-data about their input parameters
        and result data.

        For more information, see the searchable-object interface
        specification. 

      - Containment

        Database methods support URL traversal to access and invoke
        methods on individual record objects. For example, suppose you
        had an 'employees' database method that took a single argument
        'employee_id'.  Suppose that employees had a 'service_record'
        method (defined in a record class or acquired from a
        folder). The 'service_record' method could be accessed with a
        URL like::

           employees/employee_id/1234/service_record

    """
    __implements__ = (WriteLockInterface,)
    meta_type='Z SQL Method'
                
    manage=manage_main=DTMLFile('dtml/edit', globals())
    manage_main._setName('manage_main')

    __ac_permissions__=(
        ('Change Database Methods', ('manage', 'manage_main')),
    )

import Globals
Globals.InitializeClass(SQL)
