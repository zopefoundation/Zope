##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Generic Database Adapter Package Registration.

$Id$
"""

import Globals, os

classes=('DA.Connection',)
database_type='Gadfly'

class GadflyError(Exception):
    pass

class QueryError(GadflyError):
    pass

misc_={'conn':
       Globals.ImageFile('Shared/DC/ZRDB/www/DBAdapterFolder_icon.gif')}

for icon in ('table', 'view', 'stable', 'what',
             'field', 'text','bin','int','float',
             'date','time','datetime'):
    misc_[icon]=Globals.ImageFile('icons/%s.gif' % icon, globals())

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

def initialize(context):

    context.registerClass(
        DA.Connection,
        permission='Add Z Gadfly Database Connections',
        constructors=(manage_addZGadflyConnectionForm,
                      manage_addZGadflyConnection),
        legacy=(manage_addZGadflyConnectionForm,
                manage_addZGadflyConnection),
    )

# from App.config import getConfiguration
# j=os.path.join
# d=j(getConfiguration().clienthome,'gadfly')
# if not os.path.exists(d):
#     os.mkdir(d)
#     os.mkdir(j(d,'demo'))
