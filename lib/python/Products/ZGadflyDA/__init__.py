############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved. 
#
############################################################################## 
__doc__='''Generic Database Adapter Package Registration

$Id: __init__.py,v 1.4 1998/12/02 12:11:48 jim Exp $'''
__version__='$Revision: 1.4 $'[11:-2]

import Globals, ImageFile, os

classes=('DA.Connection',)
database_type='Gadfly'

misc_={'conn':
       ImageFile.ImageFile('Shared/DC/ZRDB/www/DBAdapterFolder_icon.gif')}


for icon in ('table', 'view', 'stable', 'what',
	     'field', 'text','bin','int','float',
	     'date','time','datetime'):
    misc_[icon]=ImageFile.ImageFile('icons/%s.gif' % icon, globals())

meta_types=(
    {'name':'Zope %s Database Connection' % database_type,
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

def manage_addZGadflyConnectionForm(self, REQUEST, *args, **kw):
    " "
    DA=getDA()
    return DA.addConnectionForm(
	self,REQUEST,
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
    ('Add Zope Gadfly Database Connections',
     ('manage_addZGadflyConnectionForm',
      'manage_addZGadflyConnection')),
    )

j=os.path.join
d=j(j(CUSTOMER_HOME,'var'),'gadfly')
if not os.path.exists(d):
    os.mkdir(d)
    os.mkdir(j(d,'demo'))
