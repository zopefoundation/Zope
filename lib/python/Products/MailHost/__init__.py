############################################################################## 
#
#     Copyright 
#
#       Copyright 1997 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''MailHost Product Initialization
$Id: __init__.py,v 1.4 1997/09/18 20:08:52 brian Exp $'''
__version__='$Revision: 1.4 $'[11:-2]

import MailHost

__.meta_types=  {'name':'Mail Host',
                 'action':'manage_addMailHost_form'
                 },

__.methods={
    'manage_addMailHost_form': MailHost.addForm,
    'manage_addMailHost':     MailHost.add,
    }

#$Log: __init__.py,v $
#Revision 1.4  1997/09/18 20:08:52  brian
#Added meta_type for auto-detection
#
#Revision 1.3  1997/09/09 20:49:16  jeffrey
#Changed Name from MailForm to MailHost
#Simplified interface -- removed built-in templates (for now)
#
#Revision 1.2  1997/09/09 16:09:13  jeffrey
#minor fixings
#
