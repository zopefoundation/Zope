############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
import ni, sys

import Globals, OFS.Folder, OFS.Application, App.ApplicationManager

# Open the application database
Bobobase=OFS.Application.open_bobobase()
    
try: app=Bobobase['Application']
except KeyError:
    app=OFS.Application.Application()
    app.app=App.ApplicationManager.ApplicationManager()

    Bobobase['Application']=app
    get_transaction().commit()

bobo_application=app


##############################################################################
# Revision Log
#
# $Log: Main.py,v $
# Revision 1.1  1997/08/13 18:58:39  jim
# initial
#
