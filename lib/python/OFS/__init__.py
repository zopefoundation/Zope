############################################################################## 
#
#     Copyright 
#
#       Copyright 1997 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''OFS
$Id: __init__.py,v 1.2 1997/11/10 16:32:54 jim Exp $'''
__version__='$Revision: 1.2 $'[11:-2]

import Session

__.meta_types=(
    {'name':'Session', 'action':'manage_addSessionForm'},
    {'name':'File', 'action':'manage_addFileForm'},
    {'name':'Image', 'action':'manage_addImageForm'},
    {'name':'Folder', 'action':'manage_addFolderForm'},
    {'name':'Document', 'action':'manage_addDocumentForm'},
    )
__.methods={
    'manage_addSessionForm': Session.addForm,
    'manage_addSession': Session.add,
    }





############################################################################## 
#
# $Log: __init__.py,v $
# Revision 1.2  1997/11/10 16:32:54  jim
# Changed to support separate Image and File objects.
#
# Revision 1.1  1997/11/07 19:31:42  jim
# *** empty log message ***
#
# Revision 1.1  1997/10/09 17:34:53  jim
# first cut, no testing
#
# Revision 1.1  1997/07/25 18:14:28  jim
# initial
#
#
