"""Standard management interface support

$Id: Management.py,v 1.9 1997/12/19 19:08:21 jim Exp $"""

__version__='$Revision: 1.9 $'[11:-2]

import sys,Globals
from Dialogs import MessageDialog
from Globals import HTMLFile
from Undo import UndoSupport

class Management(UndoSupport):
    """Management support"""

    manage          =HTMLFile('manage', globals())
    manage_menu     =HTMLFile('menu', globals())
    manage_tabs     =HTMLFile('manage_tabs', globals())
    manage_copyright=HTMLFile('copyright', globals())
    manage_options  =()

