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
__doc__='''Generic Database Adapter Package Registration

$Id: __init__.py,v 1.12 2001/01/08 22:47:03 brian Exp $'''
__version__='$Revision: 1.12 $'[11:-2]

import Globals, os

classes=('DA.Connection',)
database_type='Gadfly'

misc_={'conn':
       Globals.ImageFile('Shared/DC/ZRDB/www/DBAdapterFolder_icon.gif')}

for icon in ('table', 'view', 'stable', 'what',
             'field', 'text','bin','int','float',
             'date','time','datetime'):
    misc_[icon]=Globals.ImageFile('icons/%s.gif' % icon, globals())

meta_types=(
    {'name':'Z %s Database Connection' % database_type,
     'action':'manage_addZ%sConnectionForm' % database_type,
     },
    )

DA=None
def getDA():
    global DA
    if DA is None:
        home=Globals.package_home(globals())
        from gadfly import sqlwhere
        sqlwhere.filename="%s/gadfly/sql.mar" % home
        import DA
    return DA

getDA()

__module_aliases__=(
    ('Products.AqueductGadfly.DA', DA),
    )

def manage_addZGadflyConnectionForm(self, REQUEST, *args, **kw):
    " "
    DA=getDA()
    return DA.addConnectionForm(
        self, self, REQUEST,
        database_type=database_type,
        data_sources=DA.data_sources)
    
def manage_addZGadflyConnection(
    self, id, title, connection, check=None, REQUEST=None):
    " "
    return getDA().manage_addZGadflyConnection(
        self, id, title, connection, check, REQUEST)

methods={
    'manage_addZGadflyConnection':
    manage_addZGadflyConnection,
    'manage_addZGadflyConnectionForm':
    manage_addZGadflyConnectionForm,
    }

__ac_permissions__=(
    ('Add Z Gadfly Database Connections',
     ('manage_addZGadflyConnectionForm',
      'manage_addZGadflyConnection')),
    )


# j=os.path.join
# d=j(j(INSTANCE_HOME,'var'),'gadfly')
# if not os.path.exists(d):
#     os.mkdir(d)
#     os.mkdir(j(d,'demo'))
