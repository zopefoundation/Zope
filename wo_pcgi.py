##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""Try to do all of the installation steps.

This must be run from the top-level directory of the installation.
\(Yes, this is cheezy.  We'll fix this when we have a chance.

"""

import sys, os
home=os.getcwd()
print
print '-'*78
print 'Compiling py files'
import compileall
compileall.compile_dir(os.getcwd())

import build_extensions

print
print '-'*78

os.chdir(home)
data_dir=os.path.join(home, 'var')
db_path=os.path.join(data_dir, 'Data.bbb')
dd_path=os.path.join(data_dir, 'Data.bbb.in')
if not os.path.exists(data_dir):
    print 'creating data directory'
    os.mkdir('var')
    
if not os.path.exists(db_path):
    print 'creating default database'
    os.system('cp %s %s' % (dd_path, db_path))

ac_path=os.path.join(home, 'access')
if not os.path.exists(ac_path):
    print 'creating default access file'
    acfile=open(ac_path, 'w')
    acfile.write('superuser:123\n')
    acfile.close()
    os.system('chmod 744 access')

sh_path=os.path.join(home, 'start')
if not os.path.exists(sh_path):
    print 'creating start'
    s='#!/bin/sh\n%s serve.py >var/serve.log 2>var/serve.log &\n'
    shfile=open(sh_path, 'w')
    shfile.write(s % sys.executable)
    shfile.close()
    os.system('chmod 775 start')

    
print
print '-'*78
print 'NOTE: change owndership or permissions on var so that it can be'
print '      written by the web server!'
print
print "NOTE: The default super user name and password are 'superuser'"
print "      and '123'.  Create a file named 'access' in this directory"
print "      with a different super user name and password on one line"
print "      separated by a a colon. (e.g. 'spam:eggs').  You can also"
print "      specify a domain (e.g. 'spam:eggs:*.digicool.com')."
print '-'*78
print
print 'Done!'
