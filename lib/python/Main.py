############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
import sys, dcdb

dcdb.debug() # Make it easy to set a breakpoint near here.

import os
from BoboPOS import SimpleDB, TJar, SingleThreadedTransaction
import Globals

import OFS.Application

import TreeDisplay.TreeTag
import Scheduler.Scheduler

# Setup support for broken objects:
import OFS.Uninstalled, BoboPOS.PickleJar
BoboPOS.PickleJar.PickleJar.Broken=OFS.Uninstalled.Broken

# Open the application database
Bobobase=OFS.Application.open_bobobase()
SessionBase=Globals.SessionBase=TJar.TM(Bobobase)

SingleThreadedTransaction.Transaction.commit=SessionBase.committer()

bobo_application=app=Bobobase['Application']

if os.environ.has_key('BOBO_DEBUG_MODE'):
    Globals.DevelopmentMode=1
