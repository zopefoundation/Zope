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
$Id: __init__.py,v 1.1 1997/09/08 19:37:27 jeffrey Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

import MailForm

__.meta_types=  {'name':'MailForm',
                 'action':'manage_addMailFormForm'
                 },

__.methods={
    'manage_addMailFormForm': MailForm.addForm,
    'manage_addMailForm':     MailForm.add,
    }

#$log:$
