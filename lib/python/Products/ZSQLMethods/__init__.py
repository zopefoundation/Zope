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
__doc__='''SQL Method Product


$Id: __init__.py,v 1.10 1998/12/19 15:41:44 jim Exp $'''
__version__='$Revision: 1.10 $'[11:-2]
from ImageFile import ImageFile
import Shared.DC.ZRDB.Search, Shared.DC.ZRDB.Aqueduct, SQL

classes=('SQL.SQL',)

__module_aliases__=(
    ('Products.AqueductSQLMethods.SQL', SQL),
    ('Aqueduct.Aqueduct', Shared.DC.ZRDB.Aqueduct),
    ('AqueductDA.DA',     Shared.DC.ZRDB.DA),
    )

meta_types=(
    {'name':SQL.SQL.meta_type,
     'action':'manage_addZSQLMethodForm',
     },
    {'name':'Z Search Interface',
     'action':'manage_addZSearchForm'
     },
    )

methods={
    'manage_addZSQLMethod': SQL.manage_addZSQLMethod,
    'manage_addZSQLMethodForm': SQL.manage_addZSQLMethodForm,
    'SQLConnectionIDs': SQL.SQLConnectionIDs,

    
    'manage_addZSearchForm': Shared.DC.ZRDB.Search.addForm,
    'manage_addZSearch':     Shared.DC.ZRDB.Search.add,
    'ZQueryIds':             Shared.DC.ZRDB.Search.ZQueryIds,
    }

misc_={
    'icon': ImageFile('Shared/DC/ZRDB/www/DBAdapter_icon.gif'),
    }

__ac_permissions__=(
    ('Add Database Methods',
     ('manage_addZSQLMethodForm', 'manage_addZSQLMethod')),
    ('Open/Close Database Connections',   ()),
    ('Change Database Methods',           ()),
    ('Change Database Connections',           ()),
    ('Use Database Methods', ()),
    )
