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
""" Basic ZPublisher request management.

$Id$
"""

from urllib import quote
import xmlrpc
from zExceptions import Forbidden

UNSPECIFIED_ROLES=''

try:
    from ExtensionClass import Base
    class RequestContainer(Base):
        __roles__=None
        def __init__(self,**kw):
            for k,v in kw.items(): self.__dict__[k]=v

        def manage_property_types(self):
            return type_converters.keys()

except ImportError:
    class RequestContainer:
        __roles__=None
        def __init__(self,**kw):
            for k,v in kw.items(): self.__dict__[k]=v

try:
    from AccessControl.ZopeSecurityPolicy import getRoles
except ImportError:
    def getRoles(container, name, value, default):
        return getattr(value, '__roles__', default)


_marker=[]
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
    _file=None
    common={} # Common request data
    _auth=None
    _held=()

    # Allow (reluctantly) access to unprotected attributes
    __allow_access_to_unprotected_subobjects__=1

    def __init__(self, other=None, **kw):
        """The constructor is not allowed to raise errors
        """
        if other is None: other=kw
        else: other.update(kw)
        self.other=other

    def close(self):
        self.other.clear()
        self._held=None

    def processInputs(self):
        """Do any input processing that could raise errors
        """

    def __len__(self):
        return 1

    def __setitem__(self,key,value):
        """Set application variables

        This method is used to set a variable in the requests "other"
        category.
        """
        self.other[key]=value

    set=__setitem__

    def get(self, key, default=None):
        """Get a variable value

        Return a value for the required variable name.
        The value will be looked up from one of the request data
        categories. The search order is environment variables,
        other variables, form data, and then cookies.

        """
        if key=='REQUEST': return self

        v=self.other.get(key, _marker)
        if v is not _marker: return v
        v=self.common.get(key, default)
        if v is not _marker: return v

        if key=='BODY' and self._file is not None:
            p=self._file.tell()
            self._file.seek(0)
            v=self._file.read()
            self._file.seek(p)
            self.other[key]=v
            return v

        if key=='BODYFILE' and self._file is not None:
            v=self._file
            self.other[key]=v
            return v

        return default

    def __getitem__(self, key, default=_marker):
        v = self.get(key, default)
        if v is _marker:
            raise KeyError, key
        return v

    def __getattr__(self, key, default=_marker):
        v = self.get(key, default)
        if v is _marker:
            raise AttributeError, key
        return v

    def set_lazy(self, key, callable):
        pass            # MAYBE, we could do more, but let HTTPRequest do it

    def has_key(self,key):
        return self.get(key, _marker) is not _marker

    def __contains__(self, key):
        return self.has_key(key)
    
    def keys(self):
        keys = {}
        keys.update(self.common)
        keys.update(self.other)
        return keys.keys()

    def items(self):
        result = []
        get=self.get
        for k in self.keys():
            result.append((k, get(k)))
        return result

    def values(self):
        result = []
        get=self.get
        for k in self.keys():
            result.append(get(k))
        return result

    def __str__(self):
        L1 = self.items()
        L1.sort()
        return '\n'.join(map(lambda item: "%s:\t%s" % item, L1))

    __repr__=__str__


    def traverse(self, path, response=None, validated_hook=None):
        """Traverse the object space

        The REQUEST must already have a PARENTS item with at least one
        object in it.  This is typically the root object.
        """
        request=self
        request_get=request.get
        if response is None: response=self.response
        debug_mode=response.debug_mode

        # remember path for later use
        browser_path = path

        # Cleanup the path list
        if path[:1]=='/':  path=path[1:]
        if path[-1:]=='/': path=path[:-1]
        clean=[]
        for item in path.split('/'):
            # Make sure that certain things that dont make sense
            # cannot be traversed.
            if item in ('REQUEST', 'aq_self', 'aq_base'):
                return response.notFoundError(path)
            if not item or item=='.':
                continue
            elif item == '..':
                del clean[-1]
            else: clean.append(item)
        path=clean

        # How did this request come in? (HTTP GET, PUT, POST, etc.)
        method=req_method=request_get('REQUEST_METHOD', 'GET').upper()

        if method=='GET' or method=='POST' and not isinstance(response,
                                                              xmlrpc.Response):
            # Probably a browser
            no_acquire_flag=0
            # index_html is still the default method, only any object can
            # override it by implementing its own __browser_default__ method
            method = 'index_html'
        elif self.maybe_webdav_client:
            # Probably a WebDAV client.
            no_acquire_flag=1
        else:
            no_acquire_flag=0

        URL=request['URL']
        parents=request['PARENTS']
        object=parents[-1]
        del parents[:]

        roles = getRoles(None, None, object, UNSPECIFIED_ROLES)

        # if the top object has a __bobo_traverse__ method, then use it
        # to possibly traverse to an alternate top-level object.
        if hasattr(object,'__bobo_traverse__'):
            try:
                object=object.__bobo_traverse__(request)
                roles = getRoles(None, None, object, UNSPECIFIED_ROLES)
            except: pass

        if not path and not method:
            return response.forbiddenError(self['URL'])

        # Traverse the URL to find the object:
        if hasattr(object, '__of__'):
            # Try to bind the top-level object to the request
            # This is how you get 'self.REQUEST'
            object=object.__of__(RequestContainer(REQUEST=request))
        parents.append(object)

        steps=self.steps
        self._steps = _steps = map(quote, steps)
        path.reverse()

        request['TraversalRequestNameStack'] = request.path = path
        request['ACTUAL_URL'] = request['URL'] + quote(browser_path)

        # Set the posttraverse for duration of the traversal here
        self._post_traverse = post_traverse = []

        entry_name = ''
        try:
            # We build parents in the wrong order, so we
            # need to make sure we reverse it when we're doe.
            while 1:
                bpth = getattr(object, '__before_publishing_traverse__', None)
                if bpth is not None:
                    bpth(object, self)

                path = request.path = request['TraversalRequestNameStack']
                # Check for method:
                if path:
                    entry_name = path.pop()
                elif hasattr(object, '__browser_default__'):
                    # If we have reached the end of the path. We look to see
                    # if the object implements __browser_default__. If so, we
                    # call it to let the object tell us how to publish it
                    # __browser_default__ returns the object to be published
                    # (usually self) and a sequence of names to traverse to
                    # find the method to be published. (Casey)
                    request._hacked_path=1
                    object, default_path = object.__browser_default__(request)
                    if len(default_path) > 1:
                        path = list(default_path)
                        method = path.pop()
                        request['TraversalRequestNameStack'] = path
                        continue
                    else:
                        entry_name = default_path[0]
                elif (method and hasattr(object,method)
                      and entry_name != method
                      and getattr(object, method) is not None):
                    request._hacked_path=1
                    entry_name = method
                    method = 'index_html'
                else:
                    if (hasattr(object, '__call__')):
                        roles = getRoles(object, '__call__', object.__call__,
                                         roles)
                    if request._hacked_path:
                        i=URL.rfind('/')
                        if i > 0: response.setBase(URL[:i])
                    break
                step = quote(entry_name)
                _steps.append(step)
                request['URL'] = URL = '%s/%s' % (request['URL'], step)
                got = 0
                if entry_name[:1]=='_':
                    if debug_mode:
                        return response.debugError(
                          "Object name begins with an underscore at: %s" % URL)
                    else: return response.forbiddenError(entry_name)

                if hasattr(object,'__bobo_traverse__'):
                    try:
                        subobject=object.__bobo_traverse__(request,entry_name)
                        if type(subobject) is type(()) and len(subobject) > 1:
                            # Add additional parents into the path
                            parents[-1:] = list(subobject[:-1])
                            object, subobject = subobject[-2:]
                    except (AttributeError, KeyError):
                        if debug_mode:
                            return response.debugError(
                                "Cannot locate object at: %s" % URL)
                        else:
                            return response.notFoundError(URL)
                else:
                    try:
                        # Note - no_acquire_flag is necessary to support
                        # things like DAV.  We have to make sure
                        # that the target object is not acquired
                        # if the request_method is other than GET
                        # or POST. Otherwise, you could never use
                        # PUT to add a new object named 'test' if
                        # an object 'test' existed above it in the
                        # heirarchy -- you'd always get the
                        # existing object :(

                        if (no_acquire_flag and len(path) == 0 and
                            hasattr(object, 'aq_base')):
                            if hasattr(object.aq_base, entry_name):
                                subobject=getattr(object, entry_name)
                            else: raise AttributeError, entry_name
                        else: subobject=getattr(object, entry_name)
                    except AttributeError:
                        got=1
                        try: subobject=object[entry_name]
                        except (KeyError, IndexError,
                                TypeError, AttributeError):
                            if debug_mode:
                                return response.debugError(
                                    "Cannot locate object at: %s" % URL)
                            else:
                                return response.notFoundError(URL)

                # Ensure that the object has a docstring, or that the parent
                # object has a pseudo-docstring for the object. Objects that
                # have an empty or missing docstring are not published.
                doc = getattr(subobject, '__doc__', None)
                if doc is None:
                    doc = getattr(object, '%s__doc__' % entry_name, None)
                if not doc:
                    return response.debugError(
                        "The object at %s has an empty or missing " \
                        "docstring. Objects must have a docstring to be " \
                        "published." % URL
                        )

                # Hack for security: in Python 2.2.2, most built-in types
                # gained docstrings that they didn't have before. That caused
                # certain mutable types (dicts, lists) to become publishable
                # when they shouldn't be. The following check makes sure that
                # the right thing happens in both 2.2.2+ and earlier versions.

                if not typeCheck(subobject):
                    return response.debugError(
                        "The object at %s is not publishable." % URL
                        )

                roles = getRoles(
                    object, (not got) and entry_name or None, subobject,
                    roles)

                # Promote subobject to object
                object=subobject
                parents.append(object)

                steps.append(entry_name)
        finally:
            parents.reverse()
 
        # After traversal post traversal hooks aren't available anymore
        del self._post_traverse

        request['PUBLISHED'] = parents.pop(0)

        # Do authorization checks
        user=groups=None
        i=0

        if 1:  # Always perform authentication.

            last_parent_index=len(parents)
            if hasattr(object, '__allow_groups__'):
                groups=object.__allow_groups__
                inext=0
            else:
                inext=None
                for i in range(last_parent_index):
                    if hasattr(parents[i],'__allow_groups__'):
                        groups=parents[i].__allow_groups__
                        inext=i+1
                        break

            if inext is not None:
                i=inext

                if hasattr(groups, 'validate'): v=groups.validate
                else: v=old_validation

                auth=request._auth

                if v is old_validation and roles is UNSPECIFIED_ROLES:
                    # No roles, so if we have a named group, get roles from
                    # group keys
                    if hasattr(groups,'keys'): roles=groups.keys()
                    else:
                        try: groups=groups()
                        except: pass
                        try: roles=groups.keys()
                        except: pass

                    if groups is None:
                        # Public group, hack structures to get it to validate
                        roles=None
                        auth=''

                if v is old_validation:
                    user=old_validation(groups, request, auth, roles)
                elif roles is UNSPECIFIED_ROLES: user=v(request, auth)
                else: user=v(request, auth, roles)

                while user is None and i < last_parent_index:
                    parent=parents[i]
                    i=i+1
                    if hasattr(parent, '__allow_groups__'):
                        groups=parent.__allow_groups__
                    else: continue
                    if hasattr(groups,'validate'): v=groups.validate
                    else: v=old_validation
                    if v is old_validation:
                        user=old_validation(groups, request, auth, roles)
                    elif roles is UNSPECIFIED_ROLES: user=v(request, auth)
                    else: user=v(request, auth, roles)

            if user is None and roles != UNSPECIFIED_ROLES:
                response.unauthorized()

        if user is not None:
            if validated_hook is not None: validated_hook(self, user)
            request['AUTHENTICATED_USER']=user
            request['AUTHENTICATION_PATH']='/'.join(steps[:-i])

        # Remove http request method from the URL.
        request['URL']=URL

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
            raise RuntimeError, ('post_traverse() may only be called '
                                 'during publishing traversal.')
        else:
            pairs.append((f, tuple(args)))

    retry_count=0
    def supports_retry(self): return 0

    def _hold(self, object):
        """Hold a reference to an object to delay it's destruction until mine
        """
        self._held=self._held+(object,)

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
        auth=request._authUserPW()
        if auth: name,password = auth
        elif roles is None: return ''
        else: return None
    elif request.environ.has_key('REMOTE_USER'):
        name=request.environ['REMOTE_USER']
        password=None
    else:
        if roles is None: return ''
        return None

    if roles is None: return name

    keys=None
    try:
        keys=groups.keys
    except:
        try:
            groups=groups() # Maybe it was a method defining a group
            keys=groups.keys
        except: pass

    if keys is not None:
        # OK, we have a named group, so apply the roles to the named
        # group.
        if roles is UNSPECIFIED_ROLES: roles=keys()
        g=[]
        for role in roles:
            if groups.has_key(role): g.append(groups[role])
        groups=g

    for d in groups:
        if d.has_key(name) and (d[name]==password or password is None):
            return name

    if keys is None:
        # Not a named group, so don't go further
        raise Forbidden, (
            """<strong>You are not authorized to access this resource""")

    return None



# This mapping contains the built-in types that gained docstrings
# between Python 2.1 and 2.2.2. By specifically checking for these
# types during publishing, we ensure the same publishing rules in
# both versions. The downside is that this needs to be extended as
# new built-in types are added and future Python versions are
# supported. That happens rarely enough that hopefully we'll be on
# Zope 3 by then :)

import types
import sys

itypes = {}
for name in ('NoneType', 'IntType', 'LongType', 'FloatType', 'StringType',
             'BufferType', 'TupleType', 'ListType', 'DictType', 'XRangeType',
             'SliceType', 'EllipsisType', 'UnicodeType', 'CodeType',
             'TracebackType', 'FrameType', 'DictProxyType', 'BooleanType',
             'ComplexType'):
    if hasattr(types, name):
        itypes[getattr(types, name)] = 0

# Python 2.4 no longer maintains the types module.
if sys.version_info >= (2, 4):
    itypes[set] = 0
    itypes[frozenset] = 0

def typeCheck(obj, deny=itypes):
    # Return true if its ok to publish the type, false otherwise.
    return deny.get(type(obj), 1)
