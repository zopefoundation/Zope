############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''Sample product initialization module

The job of this module is to provide any run-time initialization
needed by a product and to define product meta data. 

This sample product publishes a folder-ish and a simple object.

$Id: __init__.py,v 1.1 1998/11/24 01:23:26 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

from ImageFile import ImageFile
import Ozome

# Names of objects added by this product:
meta_types=(
    {'name': Ozome.Ozome.meta_type,
     'action': 'manage_addOzomeForm', # The method to add one.     
     },
    )

# Attributes (usually "methods") to be added to folders to support
# creating objects:
methods={
    'manage_addOzomeForm': Ozome.manage_addOzomeForm,
    'manage_addOzome':     Ozome.manage_addOzome,
    }

# Permission to be added to folders:
__ac_permissions__=(
    # To add items:
    ('Add Principia Class',
     ('manage_addOzomeForm', 'manage_addOzome')),
    )



############################################################################## 
#
# $Log: __init__.py,v $
# Revision 1.1  1998/11/24 01:23:26  jim
# initial
#
# Revision 1.3  1998/06/25 11:39:15  jim
# Added permissions.
#
# Revision 1.2  1998/01/02 18:39:01  jim
# initial
#
# Revision 1.1  1997/12/31 21:57:01  jim
# initial
#
#
