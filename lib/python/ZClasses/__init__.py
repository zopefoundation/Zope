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

$Id: __init__.py,v 1.3 1999/03/22 17:45:37 jim Exp $'''
__version__='$Revision: 1.3 $'[11:-2]

from ImageFile import ImageFile
import ZClass

# Names of objects added by this product:
meta_types=(
    {'name': ZClass.ZClass.meta_type,
     'action':'manage_addZClassForm'},
    )

# Attributes (usually "methods") to be added to folders to support
# creating objects:
methods={
    'manage_addZClassForm': ZClass.manage_addZClassForm,
    'manage_addZClass': ZClass.manage_addZClass,
    'manage_subclassableClassNames': ZClass.manage_subclassableClassNames,
    
    }

# Permission to be added to folders:
__ac_permissions__=(
    # To add items:
    ('Add Zope Class',
     ('manage_addZClassForm', 'manage_addZClass',
      'manage_subclassableClassNames')),
    )

misc_={}
