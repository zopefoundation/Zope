"""Standard management interface support

$Id: Management.py,v 1.7 1997/12/05 17:10:46 brian Exp $"""

__version__='$Revision: 1.7 $'[11:-2]

import sys,Globals
from Dialogs import MessageDialog
from Globals import HTMLFile
from Undo import UndoSupport




class Management(UndoSupport):
    """Management support"""
    manage          =HTMLFile('App/manage')
    manage_menu     =HTMLFile('App/menu')
    manage_tabs     =HTMLFile('App/manage_tabs')
    manage_copyright=HTMLFile('App/copyright')
    manage_options  =()
