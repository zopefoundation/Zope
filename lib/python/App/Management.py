"""Standard management interface support

$Id: Management.py,v 1.10 1998/01/02 17:39:05 jim Exp $"""

__version__='$Revision: 1.10 $'[11:-2]

import sys,Globals
from Dialogs import MessageDialog
from Globals import HTMLFile

class Tabs:
    """Mix-in provides management folder tab support."""
    manage_tabs     =HTMLFile('manage_tabs', globals())
    manage_options  =()

class Navigation:
    """Basic (very) navigation UI support"""

    manage          =HTMLFile('manage', globals())
    manage_menu     =HTMLFile('menu', globals())
    manage_copyright=HTMLFile('copyright', globals())

