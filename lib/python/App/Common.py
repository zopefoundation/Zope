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

"""Commonly used utility functions."""

__version__='$Revision: 1.2 $'[11:-2]

from time import time, asctime, gmtime
import sys, os
from string import split, rfind


def rfc1123_date(t=None, time=time, asctime=asctime, gmtime=gmtime,
                 split=split):
    # Return an RFC 1123 format date string.
    t=split(asctime(gmtime(t or time())))
    return '%s, %s %s %s %s GMT' % (t[0],t[2],t[1],t[4],t[3])

def absattr(attr, c=callable):
    # Return the absolute value of an attribute,
    # calling the attr if it is callable.
    if c(attr):
        return attr()
    return attr

def aq_base(ob, hasattr=hasattr):
    # Return the aq_base of an object.
    if hasattr(ob, 'aq_base'):
        return ob.aq_base
    return ob

def is_acquired(ob, hasattr=hasattr, aq_base=aq_base, absattr=absattr):
    # Return true if this object is not a direct
    # subobject of its aq_parent object.
    if not hasattr(ob, 'aq_parent'):
        return 0
    if hasattr(aq_base(ob.aq_parent), absattr(ob.id)):
        return 0
    if hasattr(aq_base(ob), 'isTopLevelPrincipiaApplicationObject'):
        return 0
    return 1


def package_home(globals_dict):
    __name__=globals_dict['__name__']
    m=sys.modules[__name__]
    if hasattr(m,'__path__'):
        r=m.__path__[0]
    elif "." in __name__:
        r=sys.modules[__name__[:rfind(__name__,'.')]].__path__[0]
    else:
        r=__name__
    return os.path.join(os.getcwd(), r)


def attrget(o,name,default):
    if hasattr(o,name): return getattr(o,name)
    return default

def Dictionary(**kw): return kw # Sorry Guido
    
