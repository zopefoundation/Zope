############################################################################## 
#
#     Copyright 
#
#       Copyright 1997 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''MailForm Product Initialization
$Id: __init__.py,v 1.2 1997/09/09 16:09:13 jeffrey Exp $'''
__version__='$Revision: 1.2 $'[11:-2]

import MailForm

__.meta_types=  {'name':'MailForm',
                 'action':'manage_addMailFormForm'
                 },

__.methods={
    'manage_addMailFormForm': MailForm.addForm,
    'manage_addMailForm':     MailForm.add,
    }

#$Log: __init__.py,v $
#Revision 1.2  1997/09/09 16:09:13  jeffrey
#minor fixings
#
