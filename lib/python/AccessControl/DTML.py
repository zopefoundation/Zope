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
'''Add security system support to Document Templates

$Id: DTML.py,v 1.7 2001/06/21 17:16:31 shane Exp $''' 
__version__='$Revision: 1.7 $'[11:-2]

from DocumentTemplate import DT_Util
import SecurityManagement, string, math, whrandom, random
import DocumentTemplate.sequence

from ZopeGuards import guarded_getattr, guarded_getitem, _marker

class RestrictedDTML:
    '''
    A mix-in for derivatives of DT_String.String that adds Zope security.
    '''
    def guarded_getattr(self, ob, name, default=_marker):
        return guarded_getattr(ob, name, default)

    def guarded_getitem(self, ob, index):
        return guarded_getitem(ob, index)


# Allow access to unprotected attributes
DT_Util.TemplateDict.__allow_access_to_unprotected_subobjects__=1
string.__allow_access_to_unprotected_subobjects__=1
math.__allow_access_to_unprotected_subobjects__=1
whrandom.__allow_access_to_unprotected_subobjects__=1
random.__allow_access_to_unprotected_subobjects__=1

DocumentTemplate.sequence.__allow_access_to_unprotected_subobjects__=1

# Add security testing capabilities

class DTMLSecurityAPI:
    """API for performing security checks in DTML using '_' methods.
    """

    def SecurityValidate(md, inst, parent, name, value):
        """Validate access.

        Arguments:
        
        accessed -- the object that was being accessed
        
        container -- the object the value was found in
        
        name -- The name used to access the value
        
        value -- The value retrieved though the access.
        
        The arguments may be provided as keyword arguments. Some of these
        arguments may be ommitted, however, the policy may reject access
        in some cases when arguments are ommitted.  It is best to provide
        all the values possible.
        """
        return (SecurityManagement
                .getSecurityManager()
                .validate(inst, parent, name, value)
                )

    def SecurityValidateValue(md, value):
        """Convenience for common case of simple value validation.
        """
        return (SecurityManagement
                .getSecurityManager()
                .validateValue(value)
                )

    def SecurityCheckPermission(md, permission, object):
        """Check whether the security context allows the given permission on
        the given object.

        Arguments:
        
        permission -- A permission name
        
        object -- The object being accessed according to the permission
        """
        return (SecurityManagement
                .getSecurityManager()
                .checkPermission(permission, object)
                )

    def SecurityGetUser(md):
        """Gen the current authenticated user"""
        return (SecurityManagement
                .getSecurityManager()
                .getUser()
                )

    def SecurityCalledByExecutable(md):
        """Return a boolean value indicating if this context was called
        by an executable"""
        r = (SecurityManagement
             .getSecurityManager()
             .calledByExecutable()
             )
        if r > 0: return r-1
        return r

DT_Util.TemplateDict.__dict__.update(DTMLSecurityAPI.__dict__)

