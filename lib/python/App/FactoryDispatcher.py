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


# Implement the manage_addProduct method of object managers
import Acquisition, sys
from string import rfind
from AccessControl.PermissionMapping import aqwrap

class ProductDispatcher(Acquisition.Implicit):
    " "

    # Allow access to factory dispatchers
    __allow_access_to_unprotected_subobjects__=1

    def __getitem__(self, name):
        product=self.aq_acquire('_getProducts')()._product(name)
        dispatcher=FactoryDispatcher(product, self.aq_parent)
        return dispatcher.__of__(self)

    def __bobo_traverse__(self, REQUEST, name):
        product=self.aq_acquire('_getProducts')()._product(name)
        dispatcher=FactoryDispatcher(product, self.aq_parent, REQUEST)
        return dispatcher.__of__(self)

class FactoryDispatcher(Acquisition.Implicit):
    " "

    def __init__(self, product, dest, REQUEST=None):
        if hasattr(product,'aq_base'): product=product.aq_base
        self._product=product
        self._d=dest
        if REQUEST is not None:
            try:
                v=REQUEST['URL']
            except KeyError: pass
            else:
                v=v[:rfind(v,'/')]
                self._u=v[:rfind(v,'/')]

    def Destination(self):
        "Return the destination for factory output"
        return self.__dict__['_d'] # we don't want to wrap the result!
    this=Destination
    this__roles__=Destination__roles__=None
    

    def DestinationURL(self):
        "Return the URL for the destination for factory output"
        return self._u
    DestinationURL__roles__=None

    def __getattr__(self, name):
        p=self.__dict__['_product']
        d=p.__dict__
        if hasattr(p,name) and d.has_key(name):
            m=d[name]
            w=getattr(m, '_permissionMapper', None)
            if w is not None:
                m=ofWrapper(aqwrap(m, getattr(w,'aq_base',w), self))
    
            return m

        # Waaa
        m='Products.%s' % p.id
        if sys.modules.has_key(m) and sys.modules[m]._m.has_key(name):
            return sys.modules[m]._m[name]
    
        raise AttributeError, name

    # Provide acquired indicators for critical OM methods:
    _setObject=_getOb=Acquisition.Acquired

    # Provide a replacement for manage_main that does a redirection:
    def manage_main(trueself, self, REQUEST, update_menu=0):
        """Implement a contents view by redirecting to the true view
        """
        d = update_menu and '/manage_main?update_menu=1' or '/manage_main' 
        REQUEST['RESPONSE'].redirect(self.DestinationURL()+d)


import ExtensionClass
class ofWrapper(ExtensionClass.Base):
    def __init__(self, o):
        self._o=o

    def __of__(self, parent): return self.__dict__['_o']


