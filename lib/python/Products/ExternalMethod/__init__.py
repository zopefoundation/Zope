############################################################################## 
#
#     Copyright 
#
#       Copyright 1997 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''External Method Product Initialization
$Id: __init__.py,v 1.8 1998/11/23 16:41:16 jim Exp $'''
__version__='$Revision: 1.8 $'[11:-2]

import ExternalMethod
from ImageFile import ImageFile

classes=('ExternalMethod.ExternalMethod',)

meta_types=	{'name':'External Method',
		 'action':'manage_addExternalMethodForm'
		 },

methods={
    'manage_addExternalMethodForm':
    ExternalMethod.manage_addExternalMethodForm,
    'manage_addExternalMethod':
    ExternalMethod.manage_addExternalMethod,
    }

misc_={'function_icon':
       ImageFile('www/function.gif', globals())}


__ac_permissions__=(
    ('Add External Methods',
     ('manage_addExternalMethodForm', 'manage_addExternalMethod')),
    ('Change External Methods', ()),
    )
