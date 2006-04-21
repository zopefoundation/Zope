##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""This module implements a mix-in for traversable objects.

$Id$
"""

from urllib import quote

from AccessControl import getSecurityManager
from AccessControl import Unauthorized
from AccessControl.ZopeGuards import guarded_getattr
from Acquisition import Acquired, aq_inner, aq_parent, aq_base
from zExceptions import NotFound
from ZODB.POSException import ConflictError
from zope.interface import implements

from interfaces import ITraversable

_marker = object()


class Traversable:

    implements(ITraversable)

    absolute_url__roles__=None # Public
    def absolute_url(self, relative=0):
        """Return the absolute URL of the object.

        This a canonical URL based on the object's physical
        containment path.  It is affected by the virtual host
        configuration, if any, and can be used by external
        agents, such as a browser, to address the object.

        If the relative argument is provided, with a true value, then
        the value of virtual_url_path() is returned.

        Some Products incorrectly use '/'+absolute_url(1) as an
        absolute-path reference.  This breaks in certain virtual
        hosting situations, and should be changed to use
        absolute_url_path() instead.
        """
        if relative:
            return self.virtual_url_path()

        spp = self.getPhysicalPath()
        try:
            toUrl = self.REQUEST.physicalPathToURL
        except AttributeError:
            return path2url(spp[1:])
        return toUrl(spp)

    absolute_url_path__roles__=None # Public
    def absolute_url_path(self):
        """Return the path portion of the absolute URL of the object.

        This includes the leading slash, and can be used as an
        'absolute-path reference' as defined in RFC 2396.
        """
        spp = self.getPhysicalPath()
        try:
            toUrl = self.REQUEST.physicalPathToURL
        except AttributeError:
            return path2url(spp) or '/'
        return toUrl(spp, relative=1) or '/'

    virtual_url_path__roles__=None # Public
    def virtual_url_path(self):
        """Return a URL for the object, relative to the site root.

        If a virtual host is configured, the URL is a path relative to
        the virtual host's root object.  Otherwise, it is the physical
        path.  In either case, the URL does not begin with a slash.
        """
        spp = self.getPhysicalPath()
        try:
            toVirt = self.REQUEST.physicalPathToVirtualPath
        except AttributeError:
            return path2url(spp[1:])
        return path2url(toVirt(spp))

    getPhysicalRoot__roles__=() # Private
    getPhysicalRoot=Acquired

    getPhysicalPath__roles__=None # Public
    def getPhysicalPath(self):
        """Get the physical path of the object.

        Returns a path (an immutable sequence of strings) that can be used to
        access this object again later, for example in a copy/paste operation.
        getPhysicalRoot() and getPhysicalPath() are designed to operate
        together.
        """
        path = (self.getId(),)

        p = aq_parent(aq_inner(self))
        if p is not None:
            path = p.getPhysicalPath() + path

        return path

    unrestrictedTraverse__roles__=() # Private
    def unrestrictedTraverse(self, path, default=_marker, restricted=0):
        """Lookup an object by path.

        path -- The path to the object. May be a sequence of strings or a slash
        separated string. If the path begins with an empty path element
        (i.e., an empty string or a slash) then the lookup is performed
        from the application root. Otherwise, the lookup is relative to
        self. Two dots (..) as a path element indicates an upward traversal
        to the acquisition parent.

        default -- If provided, this is the value returned if the path cannot
        be traversed for any reason (i.e., no object exists at that path or
        the object is inaccessible).

        restricted -- If false (default) then no security checking is performed.
        If true, then all of the objects along the path are validated with
        the security machinery. Usually invoked using restrictedTraverse().
        """
        if not path:
            return self

        _getattr = getattr
        _none = None
        marker = _marker

        if isinstance(path, str):
            # Unicode paths are not allowed
            path = path.split('/')
        else:
            path = list(path)

        REQUEST = {'TraversalRequestNameStack': path}
        path.reverse()
        path_pop=path.pop

        if len(path) > 1 and not path[0]:
            # Remove trailing slash
            path.pop(0)

        if restricted:
            securityManager = getSecurityManager()
        else:
            securityManager = _none

        if not path[-1]:
            # If the path starts with an empty string, go to the root first.
            path_pop()
            self = self.getPhysicalRoot()
            if (restricted
                and not securityManager.validate(None, None, None, self)):
                raise Unauthorized, name

        try:
            obj = self
            while path:
                name = path_pop()
                __traceback_info__ = path, name

                if name[0] == '_':
                    # Never allowed in a URL.
                    raise NotFound, name

                if name == '..':
                    next = aq_parent(obj)
                    if next is not _none:
                        if restricted and not securityManager.validate(
                            obj, obj,name, next):
                            raise Unauthorized, name
                        obj = next
                        continue

                bobo_traverse = _getattr(obj, '__bobo_traverse__', _none)
                if bobo_traverse is not _none:
                    next = bobo_traverse(REQUEST, name)
                    if restricted:
                        if aq_base(next) is not next:
                            # The object is wrapped, so the acquisition
                            # context is the container.
                            container = aq_parent(aq_inner(next))
                        elif _getattr(next, 'im_self', _none) is not _none:
                            # Bound method, the bound instance
                            # is the container
                            container = next.im_self
                        elif _getattr(aq_base(obj), name, marker) == next:
                            # Unwrapped direct attribute of the object so
                            # object is the container
                            container = obj
                        else:
                            # Can't determine container
                            container = _none
                        try:
                            validated = securityManager.validate(
                                                   obj, container, name, next)
                        except Unauthorized:
                            # If next is a simple unwrapped property, it's
                            # parentage is indeterminate, but it may have been
                            # acquired safely.  In this case validate will
                            # raise an error, and we can explicitly check that
                            # our value was acquired safely.
                            validated = 0
                            if container is _none and \
                                   guarded_getattr(obj, name, marker) is next:
                                validated = 1
                        if not validated:
                            raise Unauthorized, name
                else:
                    if restricted:
                        next = guarded_getattr(obj, name, marker)
                    else:
                        next = _getattr(obj, name, marker)
                    if next is marker:
                        try:
                            next=obj[name]
                        except AttributeError:
                            # Raise NotFound for easier debugging
                            # instead of AttributeError: __getitem__
                            raise NotFound, name
                        if restricted and not securityManager.validate(
                            obj, obj, _none, next):
                            raise Unauthorized, name

                obj = next

            return obj

        except ConflictError:
            raise
        except:
            if default is not marker:
                return default
            else:
                raise

    restrictedTraverse__roles__=None # Public
    def restrictedTraverse(self, path, default=_marker):
        # Trusted code traversal code, always enforces security
        return self.unrestrictedTraverse(path, default, restricted=1)

def path2url(path):
    return '/'.join(map(quote, path))
