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
'''This module implements a mix-in for traversable objects.

$Id: Traversable.py,v 1.11 2001/09/11 14:31:25 evan Exp $'''
__version__='$Revision: 1.11 $'[11:-2]


from Acquisition import Acquired, aq_inner, aq_parent, aq_base
from AccessControl import getSecurityManager
from string import split, join
from urllib import quote

_marker=[]
StringType=type('')

class Traversable:

    absolute_url__roles__=None # Public
    def absolute_url(self, relative=0):
        try:
            req = self.REQUEST
        except AttributeError:
            req = {}
        rpp = req.get('VirtualRootPhysicalPath', ('',))
        spp = self.getPhysicalPath()
        i = 0
        for name in rpp[:len(spp)]:
            if spp[i] == name:
                i = i + 1
            else:
                break
        path = map(quote, spp[i:])
        if relative:
            # This is useful for physical path relative to a VirtualRoot
            return join(path, '/')
        return join([req['SERVER_URL']] + req._script + path, '/')

    getPhysicalRoot__roles__=() # Private
    getPhysicalRoot=Acquired

    getPhysicalPath__roles__=None # Public
    def getPhysicalPath(self):
        '''Returns a path (an immutable sequence of strings)
        that can be used to access this object again
        later, for example in a copy/paste operation.  getPhysicalRoot()
        and getPhysicalPath() are designed to operate together.
        '''
        path = (self.getId(),)
        
        p = aq_parent(aq_inner(self))
        if p is not None: 
            path = p.getPhysicalPath() + path

        return path

    unrestrictedTraverse__roles__=() # Private
    def unrestrictedTraverse(self, path, default=_marker, restricted=0):

        if not path: return self

        get=getattr
        has=hasattr
        N=None
        M=_marker

        if type(path) is StringType: path = split(path,'/')
        else: path=list(path)

        REQUEST={'TraversalRequestNameStack': path}
        path.reverse()
        pop=path.pop

        if len(path) > 1 and not path[0]:
            # Remove trailing slash
            path.pop(0)

        if restricted: securityManager=getSecurityManager()
        else: securityManager=N

        if not path[-1]:
            # If the path starts with an empty string, go to the root first.
            pop()
            self=self.getPhysicalRoot()
            if (restricted and not securityManager.validateValue(self)):
                raise 'Unauthorized', name
                    
        try:
            object = self
            while path:
                name=pop()

                if name[0] == '_':
                    # Never allowed in a URL.
                    raise 'NotFound', name

                if name=='..':
                    o=getattr(object, 'aq_parent', M)
                    if o is not M:
                        if (restricted and not securityManager.validate(
                            object, object,name, o)):
                            raise 'Unauthorized', name
                        object=o
                        continue

                t=get(object, '__bobo_traverse__', N)
                if t is not N:
                    o=t(REQUEST, name)

                    if restricted:
                        container = N
                        if has(o, 'im_self'):
                            container = o.im_self
                        elif (has(get(object, 'aq_base', object), name)
                              and get(object, name) == o):
                            container = object
                        if (not securityManager.validate(object,
                                                         container, name, o)):
                            raise 'Unauthorized', name
                      
                else:
                    o=get(object, name, M)
                    if o is not M:
                        if restricted:
                            # waaaa
                            if hasattr(aq_base(object), name):
                                # value wasn't acquired
                                if not securityManager.validate(
                                    object, object, name, o):
                                    raise 'Unauthorized', name
                            else:
                                if not securityManager.validate(
                                    object, N, name, o):
                                    raise 'Unauthorized', name
                        
                    else:
                        o=object[name]
                        if (restricted and not securityManager.validate(
                            object, object, N, o)):
                            raise 'Unauthorized', name

                object=o

            return object

        except:
            if default==_marker: raise
            return default

    restrictedTraverse__roles__=None # Public
    def restrictedTraverse(self, path, default=_marker):
        return self.unrestrictedTraverse(path, default, restricted=1)
