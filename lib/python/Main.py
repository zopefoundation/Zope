##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################
import sys, dcdb

dcdb.debug() # Make it easy to set a breakpoint near here.

import os, string
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

if os.environ.has_key('ZOPE_DATABASE_QUOTA'):
    quota=string.atoi(os.environ['ZOPE_DATABASE_QUOTA'])
    Bobobase._jar.db.set_quota(
        lambda x, quota=quota, otherdb=SessionBase.TDB:
        x + otherdb.pos > quota)
    SessionBase.TDB.set_quota(
        lambda x, quota=quota, otherdb=Bobobase._jar.db:
        x + otherdb.pos > quota)



SingleThreadedTransaction.Transaction.commit=SessionBase.committer()

bobo_application=app=Bobobase['Application']

for n in 'Z', 'BOBO':
    if os.environ.has_key('%s_DEBUG_MODE' % n):
        n=string.lower(os.environ['%s_DEBUG_MODE' % n])
        if n=='no' or n=='off': continue
        try: n=string.atoi(n)
        except: pass
        if n: Globals.DevelopmentMode=1

