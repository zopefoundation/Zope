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
$Id: __init__.py,v 1.1 1997/10/09 17:34:53 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

import ExternalMethod

__.meta_types=	{'name':'External Method',
		 'action':'manage_addExternalMethodForm'
		 },

__.methods={
    'manage_addExternalMethodForm': ExternalMethod.addForm,
    'manage_addExternalMethod':     ExternalMethod.add,
    }





############################################################################## 
#
# $Log: __init__.py,v $
# Revision 1.1  1997/10/09 17:34:53  jim
# first cut, no testing
#
# Revision 1.1  1997/07/25 18:14:28  jim
# initial
#
#
