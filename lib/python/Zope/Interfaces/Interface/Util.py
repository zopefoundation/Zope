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

from iclass import Interface, Class, ClassType, Base, assertTypeImplements
from types import FunctionType

def impliedInterface(klass, __name__=None, __doc__=None):
    """Create an interface object from a class

    The interface will contain only objects with doc strings and with names
    that begin and end with '__' or names that don't begin with '_'.
    """
    if __name__ is None: __name__="%sInterface" % klass.__name__

    if hasattr(klass, '__extends__'):
        bases = klass.__extends__
    else:
        ## Note that if your class subclasses Interfaces, then your
        ## inteface attributes will not get picked up...
        
        bases = klass.__bases__

    doc = __doc__ or klass.__doc__

    return Interface(__name__,  bases, _ii(klass, {}), doc)

def _ii(klass, items):
    for k, v in klass.__dict__.items():
        if type(v) is not FunctionType or not v.__doc__:
            continue
        if k[:1]=='_' and not (len(k) > 4 and k[:2]=='__' and k[-2:]=='__'):
            continue
        items[k]=v
    for b in klass.__bases__: _ii(b, items)
    return items
    
def implementedBy(object):        
    """Return the interfaces implemented by the object
    """
    r=[]

    t=type(object)
    if t is ClassType:
        if hasattr(object, '__class_implements__'):
            implements=object.__class_implements__
        else:
            implements=Class
    elif hasattr(object, '__implements__'):
        implements=object.__implements__
    else:
        implements=tiget(t, None)
        if implements is None: return r

    if isinstance(implements,Interface): r.append(implements)
    else: _wi(implements, r.append)

    return r

    
def implementedByInstancesOf(klass):
    """Return the interfaces that instanced implement (by default)
    """
    r=[]

    if type(klass) is ClassType:
        if hasattr(klass, '__implements__'):
            implements=klass.__implements__
        else: return r
    elif hasattr(klass, 'instancesImplements'):
        # Hook for ExtensionClass. :)
        implements=klass.instancesImplements()
    else:
        implements=tiget(klass,None)

    if implements is not None: 
        if isinstance(implements,Interface): r.append(implements)
        else: _wi(implements, r.append)

    return r


def _wi(interfaces, append):
    for i in interfaces:
        if isinstance(i,Interface): append(i)
        else: _wi(i, append)
