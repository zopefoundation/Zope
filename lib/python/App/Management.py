"""Standard management interface support

$Id: Management.py,v 1.8 1997/12/18 16:45:30 jeffrey Exp $"""

__version__='$Revision: 1.8 $'[11:-2]

import sys,Globals
from Dialogs import MessageDialog
from Globals import HTMLFile
from Undo import UndoSupport
from ImageFile import ImageFile


class Management(UndoSupport):
    """Management support"""
    # cute little tab images
    tabs_rtab=ImageFile('www/rtab.gif', globals())
    tabs_ltab=ImageFile('www/ltab.gif', globals())

    manage          =HTMLFile('manage', globals())
    manage_menu     =HTMLFile('menu', globals())
    manage_tabs     =HTMLFile('manage_tabs', globals())
    manage_copyright=HTMLFile('copyright', globals())
    manage_options  =()

    PyPoweredSmall_Gif=ImageFile('www/PythonPoweredSmall.gif', globals())
