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
__doc__='''Define Zope\'s default security policy


$Id: ZopeSecurityPolicy.py,v 1.5 2000/06/01 13:46:15 jim Exp $'''
__version__='$Revision: 1.5 $'[11:-2]

import SimpleObjectPolicies
_noroles=[]

from PermissionRole import _what_not_even_god_should_do, rolesForPermissionOn


class ZopeSecurityPolicy:
    
    def validate(self, accessed, container, name, value, context,
                 None=None, type=type, IntType=type(0), DictType=type({}),
                 getattr=getattr, _noroles=_noroles, StringType=type(''),
                 Containers=SimpleObjectPolicies.Containers,
                 valid_aq_=('aq_parent','aq_explicit')):


        ############################################################
        # Provide special rules for the acquisition attributes
        if type(name) is StringType:
            if name[:3]=='aq_' and name not in valid_aq_:
                return 0

        containerbase=getattr(container, 'aq_base', container)
        accessedbase=getattr(accessed, 'aq_base', container)

        ############################################################
        # Try to get roles
        roles=getattr(value, '__roles__', _noroles)
        if roles is _noroles:

            ############################################################
            # We have an object without roles. Presumabely, it's
            # some simple object, like a string or a list.
            if container is None: return 0 # Bail if no container

            roles=getattr(container, '__roles__', _noroles)
            if roles is _noroles:
                aq=getattr(container, 'aq_acquire', None)
                if aq is None:
                    roles=_noroles
                    if containerbase is not accessedbase: return 0
                else:
                    # Try to acquire roles
                    try: roles=aq('__roles__')
                    except AttributeError:
                        roles=_noroles
                        if containerbase is not accessedbase: return 0

            # We need to make sure that we are allowed to
            # get unprotected attributes from the container. We are
            # allowed for certain simple containers and if the
            # container says we can. Simple containers
            # may also impose name restrictions.
            p=Containers(type(container), None)
            if p is None:
                p=getattr(container,
                          '__allow_access_to_unprotected_subobjects__', None)

            if p is not None:
                tp=type(p)
                if tp is not IntType:
                    if tp is DictType:
                        p=p.get(name, None)
                    else:
                        p=p(name, value)

            if not p:
                if (containerbase is accessedbase):
                    raise 'Unauthorized', cleanupName(name, value)
                else:
                    return 0
                        
            if roles is _noroles: return 1

            # We are going to need a security-aware object to pass
            # to hasRole. We'll use the container.
            value=container

        # Short-circuit tests if we can:
        if roles is None or 'Anonymous' in roles: return 1

        # Check executable security
        stack=context.stack
        if stack:
            eo=stack[-1]

            # If the executable had an owner, can it execute?
            owner=eo.getOwner()
            if (owner is not None) and not owner.hasRole(value, roles):
                # We don't want someone to acquire if they can't
                # get an unacquired!
                if accessedbase is containerbase:
                    raise 'Unauthorized', (
                        'You are not authorized to access <em>%s</em>.' \
                        % cleanupName(name, value))
                return 0

            # Proxy roles, which are alot safer now.
            proxy_roles=getattr(eo, '_proxy_roles', None)
            if proxy_roles:
                for r in proxy_roles:
                    if r in roles: return 1
                    
                # Proxy roles actually limit access!
                if accessedbase is containerbase:
                    raise 'Unauthorized', (
                        'You are not authorized to access <em>%s</em>.' \
                        % cleanupName(name, value))
                
                return 0
                

        try:
            if context.user.hasRole(value, roles): return 1
        except AttributeError: pass

        # We don't want someone to acquire if they can't get an unacquired!
        if accessedbase is containerbase:
            raise 'Unauthorized', (
                'You are not authorized to access <em>%s</em>.' \
                % cleanupName(name, value))

        return 0

    def checkPermission(self, permission, object, context):
        roles=rolesForPermissionOn(permission, object)
        if roles is _what_not_even_god_should_do: return 0
        return context.user.has_role(roles, object)
    

def cleanupName(name, value):
    # If name is not available, tries to get it from the value.
    _name = name
    if _name is None and value is not None:
        try: _name = value.__name__
        except: pass
    return _name
