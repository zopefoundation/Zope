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

$Id: __init__.py,v 1.3 1998/11/23 15:48:18 jim Exp $'''
__version__='$Revision: 1.3 $'[11:-2]

import Globals, ImageFile, os

classes=('DA.Connection',)
database_type='Gadfly'

misc_={'conn':
       ImageFile.ImageFile('AqueductDA/www/DBAdapterFolder_icon.gif')}


for icon in ('table', 'view', 'stable', 'what',
	     'field', 'text','bin','int','float',
	     'date','time','datetime'):
    misc_[icon]=ImageFile.ImageFile('icons/%s.gif' % icon, globals())

meta_types=(
    {'name':'Aqueduct %s Database Connection' % database_type,
     'action':'manage_addAqueduct%sConnectionForm' % database_type,
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

def manage_addAqueductGadflyConnectionForm(self, REQUEST, *args, **kw):
    " "
    DA=getDA()
    return DA.addConnectionForm(
	self,REQUEST,
	database_type=database_type,
	data_sources=DA.data_sources)
    
def manage_addAqueductGadflyConnection(
    self, id, title, connection, check=None, REQUEST=None):
    " "
    return getDA().manage_addAqueductGadflyConnection(
	self, id, title, connection, check, REQUEST)

methods={
    'manage_addAqueductGadflyConnection':
    manage_addAqueductGadflyConnection,
    'manage_addAqueductGadflyConnectionForm':
    manage_addAqueductGadflyConnectionForm,
    }

__ac_permissions__=(
    ('Add Aqueduct Gadfly Database Connections',
     ('manage_addAqueductGadflyConnectionForm',
      'manage_addAqueductGadflyConnection')),
    )

j=os.path.join
d=j(j(CUSTOMER_HOME,'var'),'gadfly')
if not os.path.exists(d):
    os.mkdir(d)
    os.mkdir(j(d,'demo'))
