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
from BoboPOS2 import SimpleDB, TJar, SingleThreadedTransaction
import Globals

import OFS.Application

import TreeDisplay.TreeTag
import Scheduler.Scheduler

# Setup support for broken objects:
import OFS.Uninstalled, BoboPOS2.PickleJar
BoboPOS2.PickleJar.PickleJar.Broken=OFS.Uninstalled.Broken

# Open the application database
Bobobase=OFS.Application.open_bobobase()
SessionBase=Globals.SessionBase=TJar.TM(Bobobase)

SingleThreadedTransaction.Transaction.commit=SessionBase.committer()

bobo_application=app=Bobobase['Application']

if os.environ.has_key('PRINCIPIA_HIDE_TRACEBACKS'):
    __bobo_hide_tracebacks__=os.environ['PRINCIPIA_HIDE_TRACEBACKS']
    Globals.DevelopmentMode=1

if os.environ.has_key('PRINCIPIA_REALM'):
    __bobo_realm__=os.environ['PRINCIPIA_REALM']
