
"""Standard management interface support

$Id: Management.py,v 1.11 1998/01/08 18:00:22 jim Exp $"""

__version__='$Revision: 1.11 $'[11:-2]

import sys, Globals
from Dialogs import MessageDialog
from Globals import HTMLFile

class Tabs:
    """Mix-in provides management folder tab support."""
    manage_tabs     =HTMLFile('manage_tabs', globals())
    manage_options  =()

Globals.default__class_init__(Tabs)

class Navigation:
    """Basic (very) navigation UI support"""

    manage          =HTMLFile('manage', globals())
    manage_menu     =HTMLFile('menu', globals())
    manage_copyright=HTMLFile('copyright', globals())

Globals.default__class_init__(Navigation)
