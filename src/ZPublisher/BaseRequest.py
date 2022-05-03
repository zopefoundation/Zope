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
""" Basic ZPublisher request management.
"""

import types
from urllib.parse import quote as urllib_quote

from AccessControl.ZopeSecurityPolicy import getRoles
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition.interfaces import IAcquirer
from ExtensionClass import Base
from zExceptions import Forbidden
from zExceptions import NotFound
from zope.component import queryMultiAdapter
from zope.event import notify
from zope.interface import Interface
from zope.interface import implementer
from zope.location.interfaces import LocationError
from zope.publisher.defaultview import queryDefaultViewName
from zope.publisher.interfaces import EndRequestEvent
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import NotFound as ztkNotFound
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.traversing.namespace import namespaceLookup
from zope.traversing.namespace import nsParse
from ZPublisher.Converters import type_converters
from ZPublisher.interfaces import UseTraversalDefault
from ZPublisher.xmlrpc import is_xmlrpc_response


_marker = []
UNSPECIFIED_ROLES = ''


def quote(text):
    # quote url path segments, but leave + and @ intact
    return urllib_quote(text, '/+@')


class RequestContainer(Base):
    __roles__ = None

    def __init__(self, **kw):
        for k, v in kw.items():
            self.__dict__[k] = v

    def manage_property_types(self):
        return list(type_converters.keys())


@implementer(IBrowserPublisher)
class DefaultPublishTraverse:

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def publishTraverse(self, request, name):
        object = self.context
        URL = request['URL']

        if name[:1] == '_':
            raise Forbidden(
                "Object name begins with an underscore at: %s" % URL)

        subobject = UseTraversalDefault  # indicator
        try:
            if hasattr(object, '__bobo_traverse__'):
                try:
                    subobject = object.__bobo_traverse__(request, name)
                    if isinstance(subobject, tuple) and len(subobject) > 1:
                        # Add additional parents into the path
                        # XXX There are no tests for this:
                        request['PARENTS'][-1:] = list(subobject[:-1])
                        object, subobject = subobject[-2:]
                except (AttributeError, KeyError, NotFound) as e:
                    # Try to find a view
                    subobject = queryMultiAdapter(
                        (object, request), Interface, name)
                    if subobject is not None:
                        # OFS.Application.__bobo_traverse__ calls
                        # REQUEST.RESPONSE.notFoundError which sets the HTTP
                        # status code to 404
                        request.response.setStatus(200)
                        # We don't need to do the docstring security check
                        # for views, so lets skip it and
                        # return the object here.
                        if IAcquirer.providedBy(subobject):
                            subobject = subobject.__of__(object)
                        return subobject
                    # No view found. Reraise the error
                    # raised by __bobo_traverse__
                    raise e
        except UseTraversalDefault:
            pass
        if subobject is UseTraversalDefault:
            # No __bobo_traverse__ or default traversal requested
            # Try with an unacquired attribute:
            if hasattr(aq_base(object), name):
                subobject = getattr(object, name)
            else:
                # We try to fall back to a view:
                subobject = queryMultiAdapter((object, request), Interface,
                                              name)
                if subobject is not None:
                    if IAcquirer.providedBy(subobject):
                        subobject = subobject.__of__(object)
                    return subobject

                # And lastly, of there is no view, try acquired attributes, but
                # only if there is no __bobo_traverse__:
                try:
                    subobject = getattr(object, name)
                    # Again, clear any error status created by
                    # __bobo_traverse__ because we actually found something:
                    request.response.setStatus(200)
                except AttributeError:
                    pass

                # Lastly we try with key access:
                if subobject is None:
                    try:
                        subobject = object[name]
                    except TypeError:  # unsubscriptable
                        raise KeyError(name)

        # Ensure that the object has a docstring, or that the parent
        # object has a pseudo-docstring for the object. Objects that
        # have an empty or missing docstring are not published.
        doc = getattr(subobject, '__doc__', None)
        if not doc:
            raise Forbidden(
                "The object at %s has an empty or missing "
                "docstring. Objects must have a docstring to be "
                "published." % URL
            )

        # Check that built-in types aren't publishable.
        if not typeCheck(subobject):
            raise Forbidden(
                "The object at %s is not publishable." % URL)

        return subobject

    def browserDefault(self, request):
        if hasattr(self.context, '__browser_default__'):
            return self.context.__browser_default__(request)
        # Zope 3.2 still uses IDefaultView name when it
        # registeres default views, even though it's
        # deprecated. So we handle that here:
        default_name = queryDefaultViewName(self.context, request)
        if default_name is not None:
            # Adding '@@' here forces this to be a view.
            # A neater solution might be desireable.
            return self.context, ('@@' + default_name,)
        return self.context, ()


class BaseRequest:
    """Provide basic ZPublisher request management

    This object provides access to request data. Request data may
    vary depending on the protocol used.

    Request objects are created by the object publisher and will be
    passed to published objects through the argument name, REQUEST.

    The request object is a mapping object that represents a
    collection of variable to value mappings.
    """

    maybe_webdav_client = 1

    # While the following assignment is not strictly necessary, it
    # prevents alot of unnecessary searches because, without it,
    # acquisition of REQUEST is disallowed, which penalizes access
    # in DTML with tags.
    __roles__ = None
    _file = None
    common = {}  # Common request data
    _auth = None
    _held = ()

    # Allow (reluctantly) access to unprotected attributes
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, other=None, **kw):
        """The constructor is not allowed to raise errors
        """
        self.__doc__ = None  # Make BaseRequest objects unpublishable
        if other is None:
            other = kw
        else:
            other.update(kw)
        self.other = other

    def clear(self):
        self.other.clear()
        self._held = None

    def close(self):
        try:
            notify(EndRequestEvent(None, self))
        finally:
            # subscribers might need the zodb, so `clear` must come afterwards
            # (since `self._held=None` might close the connection, see above)
            self.clear()

    def processInputs(self):
        """Do any input processing that could raise errors
        """

    def __len__(self):
        return 1

    def __setitem__(self, key, value):
        """Set application variables

        This method is used to set a variable in the requests "other"
        category.
        """
        self.other[key] = value

    set = __setitem__

    def get(self, key, default=None):
        """Get a variable value

        Return a value for the required variable name.
        The value will be looked up from one of the request data
        categories. The search order is environment variables,
        other variables, form data, and then cookies.

        """
        if key == 'REQUEST':
            return self

        v = self.other.get(key, _marker)
        if v is not _marker:
            return v
        v = self.common.get(key, default)
        if v is not _marker:
            return v

        if key == 'BODY' and self._file is not None:
            p = self._file.tell()
            self._file.seek(0)
            v = self._file.read()
            self._file.seek(p)
            self.other[key] = v
            return v

        if key == 'BODYFILE' and self._file is not None:
            v = self._file
            self.other[key] = v
            return v

        return default

    def __getitem__(self, key, default=_marker):
        v = self.get(key, default)
        if v is _marker:
            raise KeyError(key)
        return v

    def __bobo_traverse__(self, name):
        raise KeyError(name)

    def __getattr__(self, key, default=_marker):
        v = self.get(key, default)
        if v is _marker:
            raise AttributeError(key)
        return v

    def set_lazy(self, key, callable):
        pass            # MAYBE, we could do more, but let HTTPRequest do it

    def has_key(self, key):
        return key in self

    def __contains__(self, key):
        return self.get(key, _marker) is not _marker

    def keys(self):
        keys = {}
        keys.update(self.common)
        keys.update(self.other)
        return list(keys.keys())

    def items(self):
        result = []
        for k in self.keys():
            result.append((k, self.get(k)))
        return result

    def values(self):
        result = []
        for k in self.keys():
            result.append(self.get(k))
        return result

    def __str__(self):
        L1 = list(self.items())
        L1.sort()
        return '\n'.join("%s:\t%s" % item for item in L1)

    __repr__ = __str__

    # Original version: see zope.traversing.publicationtraverse
    def traverseName(self, ob, name):
        if name and name[:1] in '@+':
            # Process URI segment parameters.
            ns, nm = nsParse(name)
            if ns:
                try:
                    ob2 = namespaceLookup(ns, nm, ob, self)
                except LocationError:
                    raise ztkNotFound(ob, name)

                if IAcquirer.providedBy(ob2):
                    ob2 = ob2.__of__(ob)
                return ob2

        if name == '.':
            return ob

        if IPublishTraverse.providedBy(ob):
            ob2 = ob.publishTraverse(self, name)
        else:
            adapter = queryMultiAdapter((ob, self), IPublishTraverse)
            if adapter is None:
                # Zope2 doesn't set up its own adapters in a lot of cases
                # so we will just use a default adapter.
                adapter = DefaultPublishTraverse(ob, self)

            ob2 = adapter.publishTraverse(self, name)

        return ob2
    traverseName__roles__ = ()

    def traverse(self, path, response=None, validated_hook=None):
        """Traverse the object space

        The REQUEST must already have a PARENTS item with at least one
        object in it.  This is typically the root object.
        """
        request = self
        request_get = request.get
        if response is None:
            response = self.response

        # remember path for later use
        browser_path = path

        # Cleanup the path list
        if path[:1] == '/':
            path = path[1:]
        if path[-1:] == '/':
            path = path[:-1]
        clean = []
        for item in path.split('/'):
            # Make sure that certain things that dont make sense
            # cannot be traversed.
            if item in ('REQUEST', 'aq_self', 'aq_base'):
                return response.notFoundError(path)
            if not item or item == '.':
                continue
            elif item == '..':
                del clean[-1]
            else:
                clean.append(item)
        path = clean

        # How did this request come in? (HTTP GET, PUT, POST, etc.)
        method = request_get('REQUEST_METHOD', 'GET').upper()

        # Probably a browser
        no_acquire_flag = 0
        if method in ('GET', 'POST', 'PURGE') and \
           not is_xmlrpc_response(response):
            # index_html is still the default method, only any object can
            # override it by implementing its own __browser_default__ method
            method = 'index_html'
        elif method != 'HEAD' and self.maybe_webdav_client:
            # Probably a WebDAV client.
            no_acquire_flag = 1

        URL = request['URL']
        parents = request['PARENTS']
        object = parents[-1]
        del parents[:]

        self.roles = getRoles(None, None, object, UNSPECIFIED_ROLES)

        # if the top object has a __bobo_traverse__ method, then use it
        # to possibly traverse to an alternate top-level object.
        if hasattr(object, '__bobo_traverse__'):
            try:
                new_object = object.__bobo_traverse__(request)
                if new_object is not None:
                    object = new_object
                    self.roles = getRoles(None, None, object,
                                          UNSPECIFIED_ROLES)
            except Exception:
                pass

        if not path and not method:
            return response.forbiddenError(self['URL'])

        # Traverse the URL to find the object:
        if hasattr(object, '__of__'):
            # Try to bind the top-level object to the request
            # This is how you get 'self.REQUEST'
            object = object.__of__(RequestContainer(REQUEST=request))
        parents.append(object)

        steps = self.steps
        self._steps = _steps = list(map(quote, steps))
        path.reverse()

        request['TraversalRequestNameStack'] = request.path = path
        request['ACTUAL_URL'] = request['URL'] + quote(browser_path)

        # Set the posttraverse for duration of the traversal here
        self._post_traverse = post_traverse = []

        entry_name = ''
        try:
            # We build parents in the wrong order, so we
            # need to make sure we reverse it when we're done.
            while 1:
                bpth = getattr(object, '__before_publishing_traverse__', None)
                if bpth is not None:
                    bpth(object, self)

                path = request.path = request['TraversalRequestNameStack']
                # Check for method:
                if path:
                    entry_name = path.pop()
                else:
                    # If we have reached the end of the path, we look to see
                    # if we can find IBrowserPublisher.browserDefault. If so,
                    # we call it to let the object tell us how to publish it.
                    # BrowserDefault returns the object to be published
                    # (usually self) and a sequence of names to traverse to
                    # find the method to be published.

                    # This is webdav support. The last object in the path
                    # should not be acquired. Instead, a NullResource should
                    # be given if it doesn't exist:
                    if no_acquire_flag and \
                       hasattr(object, 'aq_base') and \
                       not hasattr(object, '__bobo_traverse__'):

                        if (object.__parent__ is not
                                aq_inner(object).__parent__):
                            from webdav.NullResource import NullResource
                            object = NullResource(parents[-2], object.getId(),
                                                  self).__of__(parents[-2])

                    if IBrowserPublisher.providedBy(object):
                        adapter = object
                    else:
                        adapter = queryMultiAdapter((object, self),
                                                    IBrowserPublisher)
                        if adapter is None:
                            # Zope2 doesn't set up its own adapters in a lot
                            # of cases so we will just use a default adapter.
                            adapter = DefaultPublishTraverse(object, self)

                    object, default_path = adapter.browserDefault(self)
                    if default_path:
                        request._hacked_path = 1
                        if len(default_path) > 1:
                            path = list(default_path)
                            method = path.pop()
                            request['TraversalRequestNameStack'] = path
                            continue
                        else:
                            entry_name = default_path[0]
                    elif (method
                          and hasattr(object, method)
                          and entry_name != method
                          and getattr(object, method) is not None):
                        request._hacked_path = 1
                        entry_name = method
                        method = 'index_html'
                    else:
                        if hasattr(object, '__call__'):
                            self.roles = getRoles(
                                object, '__call__',
                                object.__call__, self.roles)
                        if request._hacked_path:
                            i = URL.rfind('/')
                            if i > 0:
                                response.setBase(URL[:i])
                        break
                step = quote(entry_name)
                _steps.append(step)
                request['URL'] = URL = f'{request["URL"]}/{step}'

                try:
                    subobject = self.traverseName(object, entry_name)
                    if hasattr(object, '__bobo_traverse__') or \
                       hasattr(object, entry_name):
                        check_name = entry_name
                    else:
                        check_name = None

                    self.roles = getRoles(
                        object, check_name, subobject,
                        self.roles)
                    object = subobject
                # traverseName() might raise ZTK's NotFound
                except (KeyError, AttributeError, ztkNotFound):
                    if response.debug_mode:
                        return response.debugError(
                            "Cannot locate object at: %s" % URL)
                    else:
                        return response.notFoundError(URL)
                except Forbidden as e:
                    if self.response.debug_mode:
                        return response.debugError(e.args)
                    else:
                        return response.forbiddenError(entry_name)

                parents.append(object)

                steps.append(entry_name)
        finally:
            parents.reverse()

        # Note - no_acquire_flag is necessary to support
        # things like DAV.  We have to make sure
        # that the target object is not acquired
        # if the request_method is other than GET
        # or POST. Otherwise, you could never use
        # PUT to add a new object named 'test' if
        # an object 'test' existed above it in the
        # hierarchy -- you'd always get the
        # existing object :(
        if no_acquire_flag and \
           hasattr(parents[1], 'aq_base') and \
           not hasattr(parents[1], '__bobo_traverse__'):
            base = aq_base(parents[1])
            if not hasattr(base, entry_name):
                try:
                    if entry_name not in base:
                        raise AttributeError(entry_name)
                except TypeError:
                    raise AttributeError(entry_name)

        # After traversal post traversal hooks aren't available anymore
        del self._post_traverse

        request['PUBLISHED'] = parents.pop(0)

        # Do authorization checks
        user = groups = None
        i = 0

        if 1:  # Always perform authentication.

            last_parent_index = len(parents)
            if hasattr(object, '__allow_groups__'):
                groups = object.__allow_groups__
                inext = 0
            else:
                inext = None
                for i in range(last_parent_index):
                    if hasattr(parents[i], '__allow_groups__'):
                        groups = parents[i].__allow_groups__
                        inext = i + 1
                        break

            if inext is not None:
                i = inext
                v = getattr(groups, 'validate', old_validation)

                auth = request._auth

                if v is old_validation and self.roles is UNSPECIFIED_ROLES:
                    # No roles, so if we have a named group, get roles from
                    # group keys
                    if hasattr(groups, 'keys'):
                        self.roles = list(groups.keys())
                    else:
                        try:
                            groups = groups()
                        except Exception:
                            pass
                        try:
                            self.roles = list(groups.keys())
                        except Exception:
                            pass

                    if groups is None:
                        # Public group, hack structures to get it to validate
                        self.roles = None
                        auth = ''

                if v is old_validation:
                    user = old_validation(groups, request, auth, self.roles)
                elif self.roles is UNSPECIFIED_ROLES:
                    user = v(request, auth)
                else:
                    user = v(request, auth, self.roles)

                while user is None and i < last_parent_index:
                    parent = parents[i]
                    i = i + 1
                    if hasattr(parent, '__allow_groups__'):
                        groups = parent.__allow_groups__
                    else:
                        continue
                    if hasattr(groups, 'validate'):
                        v = groups.validate
                    else:
                        v = old_validation
                    if v is old_validation:
                        user = old_validation(
                            groups, request, auth, self.roles)
                    elif self.roles is UNSPECIFIED_ROLES:
                        user = v(request, auth)
                    else:
                        user = v(request, auth, self.roles)

            if user is None and self.roles != UNSPECIFIED_ROLES:
                response.unauthorized()

        if user is not None:
            if validated_hook is not None:
                validated_hook(self, user)
            request['AUTHENTICATED_USER'] = user
            request['AUTHENTICATION_PATH'] = '/'.join(steps[:-i])

        # Remove http request method from the URL.
        request['URL'] = URL

        # Run post traversal hooks
        if post_traverse:
            result = exec_callables(post_traverse)
            if result is not None:
                object = result

        return object

    def post_traverse(self, f, args=()):
        """Add a callable object and argument tuple to be post-traversed.

        If traversal and authentication succeed, each post-traversal
        pair is processed in the order in which they were added.
        Each argument tuple is passed to its callable.  If a callable
        returns a value other than None, no more pairs are processed,
        and the return value replaces the traversal result.
        """
        try:
            pairs = self._post_traverse
        except AttributeError:
            raise RuntimeError('post_traverse() may only be called '
                               'during publishing traversal.')
        else:
            pairs.append((f, tuple(args)))

    retry_count = 0

    def supports_retry(self):
        return 0

    def _hold(self, object):
        """Hold a reference to an object to delay it's destruction until mine
        """
        if self._held is not None:
            self._held = self._held + (object, )


def exec_callables(callables):
    result = None
    for (f, args) in callables:
        # Don't catch exceptions here. And don't hide them anyway.
        result = f(*args)
        if result is not None:
            return result


def old_validation(groups, request, auth,
                   roles=UNSPECIFIED_ROLES):

    if auth:
        auth = request._authUserPW()
        if auth:
            name, password = auth
        elif roles is None:
            return ''
        else:
            return None
    elif 'REMOTE_USER' in request.environ:
        name = request.environ['REMOTE_USER']
        password = None
    else:
        if roles is None:
            return ''
        return None

    if roles is None:
        return name

    keys = None
    try:
        keys = groups.keys
    except Exception:
        try:
            groups = groups()  # Maybe it was a method defining a group
            keys = groups.keys
        except Exception:
            pass

    if keys is not None:
        # OK, we have a named group, so apply the roles to the named
        # group.
        if roles is UNSPECIFIED_ROLES:
            roles = keys()
        g = []
        for role in roles:
            if role in groups:
                g.append(groups[role])
        groups = g

    for d in groups:
        if name in d and (d[name] == password or password is None):
            return name

    if keys is None:
        # Not a named group, so don't go further
        raise Forbidden(
            """<strong>You are not authorized to access this resource""")

    return None


itypes = {
    bool: 0,
    types.CodeType: 0,
    complex: 0,
    dict: 0,
    float: 0,
    types.FrameType: 0,
    frozenset: 0,
    int: 0,
    list: 0,
    type(None): 0,
    set: 0,
    slice: 0,
    str: 0,
    types.TracebackType: 0,
    tuple: 0,
}
for name in ('BufferType', 'DictProxyType', 'EllipsisType',
             'LongType', 'UnicodeType', 'XRangeType'):
    if hasattr(types, name):
        itypes[getattr(types, name)] = 0


def typeCheck(obj, deny=itypes):
    # Return true if its ok to publish the type, false otherwise.
    return deny.get(type(obj), 1)
