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
"""
Objects for packages that have been uninstalled.
"""
import string, SimpleItem, Globals, Acquisition
import Persistence

broken_klasses={}

class BrokenClass(Acquisition.Explicit, SimpleItem.Item, 
                  Persistence.Persistent):
    _p_changed=0
    meta_type='Broken Because Product is Gone'
    icon='p_/broken'
    product_name='unknown'
    id='broken'

    def __getstate__(self):
        raise SystemError, (
            """This object was originally created by a product that
            is no longer installed.  It cannot be updated.
            """)

    def __getattr__(self, name):
        if name[:3]=='_p_':
            return BrokenClass.inheritedAttribute('__getattr__')(self, name)
        raise AttributeError, name

    manage=manage_main=Globals.HTMLFile('brokenEdit',globals())
    manage_workspace=manage
    

def Broken(self, oid, klass):
    if broken_klasses.has_key(klass):
        klass=broken_klasses[klass]
    else:
        module, klass = klass
        d={'BrokenClass': BrokenClass}
        exec ("class %s(BrokenClass): ' '; __module__=%s"
              % (klass, `module`)) in d
        broken_klasses[klass]=d[klass]
        klass=d[klass]
        module=string.split(module,'.')
        if len(module) > 2 and module[0]=='Products':
            klass.product_name= module[1]
        klass.title=(
            'This object from the <strong>%s</strong> product '
            'is <strong><font color=red>broken</font></strong>!' %
            klass.product_name)
        klass.info=(
            'This object\'s class was %s in module %s.' %
            (klass.__name__, klass.__module__))

    if oid is None: return klass
    i=klass()
    i._p_oid=oid
    i._p_jar=self
    return i

