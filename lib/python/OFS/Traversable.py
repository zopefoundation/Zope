##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
'''This module implements a mix-in for traversable objects.

$Id: Traversable.py,v 1.17 2002/09/18 15:48:59 shane Exp $'''
__version__='$Revision: 1.17 $'[11:-2]


from Acquisition import Acquired, aq_inner, aq_parent, aq_base
from AccessControl import getSecurityManager
from AccessControl import Unauthorized
from AccessControl.ZopeGuards import guarded_getattr
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
            return '/'.join(path)
        return '/'.join([req['SERVER_URL']] + req._script + path)

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

        if type(path) is StringType: path = path.split('/')
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
                raise Unauthorized, name

        try:
            object = self
            while path:
                name=pop()
                __traceback_info__ = path, name

                if name[0] == '_':
                    # Never allowed in a URL.
                    raise 'NotFound', name

                if name=='..':
                    o=getattr(object, 'aq_parent', M)
                    if o is not M:
                        if (restricted and not securityManager.validate(
                            object, object,name, o)):
                            raise Unauthorized, name
                        object=o
                        continue

                t=get(object, '__bobo_traverse__', N)
                if t is not N:
                    o=t(REQUEST, name)

                    if restricted:
                        container = N
                        if aq_base(o) is not o:
                            # The object is wrapped, so the acquisition
                            # context determines the container.
                            container = aq_parent(aq_inner(o))
                        elif has(o, 'im_self'):
                            container = o.im_self
                        elif (has(get(object, 'aq_base', object), name)
                              and get(object, name) == o):
                            container = object
                        if (not securityManager.validate(object,
                                                         container, name, o)):
                            raise Unauthorized, name

                else:
                    if restricted:
                        o = guarded_getattr(object, name, M)
                    else:
                        o = get(object, name, M)
                    if o is M:
                        o=object[name]
                        if (restricted and not securityManager.validate(
                            object, object, N, o)):
                            raise Unauthorized, name

                object=o

            return object

        except:
            if default==_marker: raise
            return default

    restrictedTraverse__roles__=None # Public
    def restrictedTraverse(self, path, default=_marker):
        return self.unrestrictedTraverse(path, default, restricted=1)
