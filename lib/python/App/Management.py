
"""Standard management interface support

$Id: Management.py,v 1.12 1998/06/11 20:29:55 jim Exp $"""

__version__='$Revision: 1.12 $'[11:-2]

import sys, Globals
from Dialogs import MessageDialog
from Globals import HTMLFile
from string import split, join

class Tabs:
    """Mix-in provides management folder tab support."""
    manage_tabs     =HTMLFile('manage_tabs', globals())
    manage_options  =()
    def tabs_path_info(self, script, path):
        url=script
        out=[]
        while path[:1]=='/': path=path[1:]
        while path[-1:]=='/': path=path[:-1]
        while script[:1]=='/': script=script[1:]
        while script[-1:]=='/': script=script[:-1]
        path=split(path,'/')[:-1]
        if path: path=[script]+path
        else: path=[script]
        script=''
        last=path[-1]
        del path[-1]
        for p in path:
            script="%s/%s" % (script, p)
            out.append('<a href="%s/manage_main">%s</a>' % (script, p))
        out.append(last)
        return join(out,'&nbsp;/&nbsp;')
                
        

Globals.default__class_init__(Tabs)

class Navigation:
    """Basic (very) navigation UI support"""

    manage          =HTMLFile('manage', globals())
    manage_menu     =HTMLFile('menu', globals())
    manage_copyright=HTMLFile('copyright', globals())

Globals.default__class_init__(Navigation)
