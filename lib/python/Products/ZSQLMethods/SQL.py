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
__doc__='''SQL Methods


$Id: SQL.py,v 1.8 1998/12/16 15:29:22 jim Exp $'''
__version__='$Revision: 1.8 $'[11:-2]

import Shared.DC.ZRDB.DA
from Globals import HTMLFile

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

manage_addZSQLMethodForm=HTMLFile('add', globals())
def manage_addZSQLMethod(self, id, title,
                                connection_id, arguments, template,
                                REQUEST=None):
    """Add an SQL Method

    The 'connection_id' argument is the id of a database connection
    that resides in the current folder or in a folder above the
    current folder.  The database should understand SQL.

    The 'arguments' argument is a string containing an arguments
    specification, as would be given in the SQL method cration form.

    The 'template' argument is a string containing the source for the
    SQL Template.
    """
    self._setObject(id, SQL(id, title, connection_id, arguments, template))
    if REQUEST is not None: return self.manage_main(self,REQUEST)

class SQL(Shared.DC.ZRDB.DA.DA):
    """SQL Database methods

    SQL Database methods are used to access external SQL databases.

    They support three important Principia abstractions:

      - Method

        SQL Methods behave like methods of the folders they are
        accessed in.  In particular, they can be used from other
        methods, like Documents, ExternalMethods, and even other SQL
        Methods.

      - Searchability

        Database methods support the Principia Searchable Object
        Interface.  Search interface wizards can be used to build user
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
    meta_type='Z SQL Method'
    icon='misc_/ZSQLMethods/icon'
                
    manage_main=HTMLFile('edit', globals())

