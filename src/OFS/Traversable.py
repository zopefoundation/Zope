##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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
"""

from urllib.parse import quote

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.unauthorized import Unauthorized
from AccessControl.ZopeGuards import guarded_getattr
from Acquisition import Acquired
from Acquisition import aq_acquire
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition.interfaces import IAcquirer
from OFS.interfaces import IApplication
from OFS.interfaces import ITraversable
from zExceptions import NotFound
from ZODB.POSException import ConflictError
from zope.component import queryMultiAdapter
from zope.interface import Interface
from zope.interface import implementer
from zope.location.interfaces import LocationError
from zope.traversing.namespace import namespaceLookup
from zope.traversing.namespace import nsParse
from ZPublisher.interfaces import UseTraversalDefault


_marker = object()


@implementer(ITraversable)
class Traversable:

    security = ClassSecurityInfo()

    @security.public
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
            toUrl = aq_acquire(self, 'REQUEST').physicalPathToURL
        except AttributeError:
            return path2url(spp[1:])
        return toUrl(spp)

    @security.public
    def absolute_url_path(self):
        """Return the path portion of the absolute URL of the object.

        This includes the leading slash, and can be used as an
        'absolute-path reference' as defined in RFC 2396.
        """
        spp = self.getPhysicalPath()
        try:
            toUrl = aq_acquire(self, 'REQUEST').physicalPathToURL
        except AttributeError:
            return path2url(spp) or '/'
        return toUrl(spp, relative=1) or '/'

    @security.public
    def virtual_url_path(self):
        """Return a URL for the object, relative to the site root.

        If a virtual host is configured, the URL is a path relative to
        the virtual host's root object.  Otherwise, it is the physical
        path.  In either case, the URL does not begin with a slash.
        """
        spp = self.getPhysicalPath()
        try:
            toVirt = aq_acquire(self, 'REQUEST').physicalPathToVirtualPath
        except AttributeError:
            return path2url(spp[1:])
        return path2url(toVirt(spp))

    # decorators did not work on variables
    security.declarePrivate('getPhysicalRoot')  # NOQA: D001
    getPhysicalRoot = Acquired

    @security.public
    def getPhysicalPath(self):
        # Get the physical path of the object.
        #
        # Returns a path (an immutable sequence of strings) that can be used to
        # access this object again later, for example in a copy/paste
        # operation.  getPhysicalRoot() and getPhysicalPath() are designed to
        # operate together.

        # This implementation is optimized to avoid excessive amounts of
        # function calls while walking up from an object on a deep level.
        try:
            id = self.id or self.getId()
        except AttributeError:
            id = self.getId()

        path = (id, )
        p = aq_parent(aq_inner(self))
        if p is None:
            return path

        func = self.getPhysicalPath.__func__
        while p is not None:
            if func is p.getPhysicalPath.__func__:
                try:
                    pid = p.id or p.getId()
                except AttributeError:
                    pid = p.getId()

                path = (pid, ) + path
                p = aq_parent(aq_inner(p))
            else:
                if IApplication.providedBy(p):
                    path = ('', ) + path
                else:
                    path = p.getPhysicalPath() + path
                break

        return path

    @security.private
    def unrestrictedTraverse(self, path, default=_marker, restricted=False):
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

        restricted -- If false (default) then no security checking is
        performed. If true, then all of the objects along the path are
        validated with the security machinery. Usually invoked using
        restrictedTraverse().
        """
        if not path:
            return self

        if isinstance(path, str):
            path = path.split('/')
        else:
            path = list(path)
            for part in path:
                if not isinstance(part, str):
                    raise TypeError(
                        "path should be a string or an iterable of strings"
                    )

        REQUEST = {'TraversalRequestNameStack': path}
        path.reverse()
        path_pop = path.pop

        if len(path) > 1 and not path[0]:
            # Remove trailing slash
            path_pop(0)

        if restricted:
            validate = getSecurityManager().validate

        if not path[-1]:
            # If the path starts with an empty string, go to the root first.
            path_pop()
            obj = self.getPhysicalRoot()
            if restricted:
                validate(None, None, None, obj)  # may raise Unauthorized
        else:
            obj = self

        # import time ordering problem
        from webdav.NullResource import NullResource
        resource = _marker

        try:
            while path:
                name = path_pop()
                __traceback_info__ = path, name

                if name[0] == '_':
                    # Never allowed in a URL.
                    raise NotFound(name)

                if name == '..':
                    next = aq_parent(obj)
                    if next is not None:
                        if restricted and not validate(obj, obj, name, next):
                            raise Unauthorized(name)
                        obj = next
                        continue

                bobo_traverse = getattr(obj, '__bobo_traverse__', None)
                try:
                    if (
                        name
                        and name[:1] in '@+'
                        and name != '+'
                        and nsParse(name)[1]
                    ):
                        # Process URI segment parameters.
                        ns, nm = nsParse(name)
                        try:
                            next = namespaceLookup(
                                ns, nm, obj, aq_acquire(self, 'REQUEST'))
                            if IAcquirer.providedBy(next):
                                next = next.__of__(obj)
                            if restricted and not validate(
                                    obj, obj, name, next):
                                raise Unauthorized(name)
                        except LocationError:
                            raise AttributeError(name)

                    else:
                        next = UseTraversalDefault  # indicator
                        try:
                            if bobo_traverse is not None:
                                next = bobo_traverse(REQUEST, name)
                                if restricted:
                                    if aq_base(next) is not next:
                                        # The object is wrapped, so the
                                        # acquisition context is the container.
                                        container = aq_parent(aq_inner(next))
                                    elif getattr(next, '__self__',
                                                 None) is not None:
                                        # Bound method, the bound instance
                                        # is the container
                                        container = next.__self__
                                    elif getattr(
                                            aq_base(obj),
                                            name, _marker) is next:
                                        # Unwrapped direct attribute of the
                                        # object so object is the container
                                        container = obj
                                    else:
                                        # Can't determine container
                                        container = None
                                    # If next is a simple unwrapped property,
                                    # its parentage is indeterminate, but it
                                    # may have been acquired safely. In this
                                    # case validate will raise an error, and
                                    # we can explicitly check that our value
                                    # was acquired safely.
                                    try:
                                        ok = validate(
                                            obj, container, name, next)
                                    except Unauthorized:
                                        ok = False
                                    if not ok:
                                        if (
                                            container is not None
                                            or guarded_getattr(obj, name, _marker) is not next  # NOQA: E501
                                        ):
                                            raise Unauthorized(name)
                        except UseTraversalDefault:
                            # behave as if there had been no
                            # '__bobo_traverse__'
                            bobo_traverse = None
                        if next is UseTraversalDefault:
                            if getattr(
                                    aq_base(obj),
                                    name, _marker) is not _marker:
                                if restricted:
                                    next = guarded_getattr(obj, name)
                                else:
                                    next = getattr(obj, name)
                            else:
                                try:
                                    next = obj[name]
                                    # The item lookup may return a
                                    # NullResource, if this is the case we
                                    # save it and return it if all other
                                    # lookups fail.
                                    if isinstance(next, NullResource):
                                        resource = next
                                        raise KeyError(name)
                                except (AttributeError, TypeError):
                                    # Raise NotFound for easier debugging
                                    # instead of AttributeError: __getitem__
                                    # or TypeError: not subscriptable
                                    raise NotFound(name)
                                if restricted and not validate(
                                        obj, obj, None, next):
                                    raise Unauthorized(name)

                except (AttributeError, NotFound, KeyError) as e:
                    # Try to look for a view
                    next = queryMultiAdapter(
                        (obj, aq_acquire(self, 'REQUEST')),
                        Interface, name)

                    if next is not None:
                        if IAcquirer.providedBy(next):
                            next = next.__of__(obj)
                        if restricted and not validate(obj, obj, name, next):
                            raise Unauthorized(name)
                    elif bobo_traverse is not None:
                        # Attribute lookup should not be done after
                        # __bobo_traverse__:
                        raise e
                    else:
                        # No view, try acquired attributes
                        try:
                            if restricted:
                                next = guarded_getattr(obj, name, _marker)
                            else:
                                next = getattr(obj, name, _marker)
                        except AttributeError:
                            raise e
                        if next is _marker:
                            # If we have a NullResource from earlier use it.
                            next = resource
                            if next is _marker:
                                # Nothing found re-raise error
                                raise e

                obj = next

            return obj

        except ConflictError:
            raise
        except Exception:
            if default is not _marker:
                return default
            else:
                raise

    @security.public
    def restrictedTraverse(self, path, default=_marker):
        # Trusted code traversal code, always enforces securitys
        return self.unrestrictedTraverse(path, default, restricted=True)


InitializeClass(Traversable)


def path2url(path):
    return '/'.join(map(quote, path))
