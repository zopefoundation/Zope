##############################################################################
#
# Copyright (c) 2002-2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" HTTP request management.
"""

import codecs
import os
import random
import re
import time
from cgi import FieldStorage

from six import PY2
from six import PY3
from six import binary_type
from six import string_types
from six import text_type
from six import reraise
from six.moves.urllib.parse import unquote
from six.moves.urllib.parse import urlparse

from AccessControl.tainted import should_be_tainted as base_should_be_tainted
from AccessControl.tainted import taint_string
from zope.component import queryUtility
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.locales import LoadLocaleError
from zope.i18n.locales import locales
from zope.interface import directlyProvidedBy
from zope.interface import directlyProvides
from zope.interface import implementer
from zope.publisher.base import DebugFlags
from zope.publisher.interfaces.browser import IBrowserRequest
from ZPublisher import xmlrpc
from ZPublisher.BaseRequest import BaseRequest
from ZPublisher.BaseRequest import quote
from ZPublisher.interfaces import IXmlrpcChecker, RequestParameterError
from ZPublisher.utils import basic_auth_decode


if PY3:
    from html import escape
else:
    from cgi import escape

# This may get overwritten during configuration
default_encoding = 'utf-8'

isCGI_NAMEs = {
    'SERVER_SOFTWARE': 1,
    'SERVER_NAME': 1,
    'GATEWAY_INTERFACE': 1,
    'SERVER_PROTOCOL': 1,
    'SERVER_PORT': 1,
    'REQUEST_METHOD': 1,
    'PATH_INFO': 1,
    'PATH_TRANSLATED': 1,
    'SCRIPT_NAME': 1,
    'QUERY_STRING': 1,
    'REMOTE_HOST': 1,
    'REMOTE_ADDR': 1,
    'AUTH_TYPE': 1,
    'REMOTE_USER': 1,
    'REMOTE_IDENT': 1,
    'CONTENT_TYPE': 1,
    'CONTENT_LENGTH': 1,
    'SERVER_URL': 1,
}

isCGI_NAME = isCGI_NAMEs.__contains__

hide_key = {'HTTP_AUTHORIZATION': 1, 'HTTP_CGI_AUTHORIZATION': 1}

default_port = {'http': 80, 'https': 443}

tainting_env = str(os.environ.get('ZOPE_DTML_REQUEST_AUTOQUOTE', '')).lower()
TAINTING_ENABLED = tainting_env not in ('disabled', '0', 'no')

_marker = []

# The trusted_proxies configuration setting contains a sequence
# of front-end proxies that are trusted to supply an accurate
# X_FORWARDED_FOR header. If REMOTE_ADDR is one of the values in this list
# and it has set an X_FORWARDED_FOR header, ZPublisher copies REMOTE_ADDR
# into X_FORWARDED_BY, and the last element of the X_FORWARDED_FOR list
# into REMOTE_ADDR. X_FORWARDED_FOR is left unchanged.
# The ZConfig machinery may sets this attribute on initialization
# if any trusted-proxies are defined in the configuration file.

trusted_proxies = []


class NestedLoopExit(Exception):
    pass


def splitport(url):
    """Return (hostname, port) from a URL

    If it does not return a port, return the URL unchanged.
    This mimics the behavior of the `splitport` function which was
    in Python and got deprecated in Python 3.8.
    """
    parsed = urlparse(url)
    if (not parsed.scheme
            and parsed.port is None
            and parsed.hostname is None):
        # urlparse does not like URLs without a protocol, so add one:
        parsed = urlparse('http://{}'.format(url))
    if parsed.port is None:
        return url, None
    hostname = parsed.hostname
    if parsed.netloc.startswith('['):
        hostname = "[{}]".format(hostname)
    return hostname, parsed.port


@implementer(IBrowserRequest)
class HTTPRequest(BaseRequest):
    """ Model HTTP request data.

    This object provides access to request data.  This includes, the
    input headers, form data, server data, and cookies.

    Request objects are created by the object publisher and will be
    passed to published objects through the argument name, REQUEST.

    The request object is a mapping object that represents a
    collection of variable to value mappings.  In addition, variables
    are divided into five categories:

      - Environment variables

        These variables include input headers, server data, and other
        request-related data.  The variable names are as specified
        in the <a href="https://tools.ietf.org/html/rfc3875">CGI
        specification</a>

      - Form data

        These are data extracted from either a URL-encoded query
        string or body, if present.

      - Cookies

        These are the cookie data, if present.

      - Lazy Data

        These are callables which are deferred until explicitly
        referenced, at which point they are resolved and stored as
        application data.

      - Other

        Data that may be set by an application object.

    The form attribute of a request is actually a Field Storage
    object.  When file uploads are used, this provides a richer and
    more complex interface than is provided by accessing form data as
    items of the request.  See the FieldStorage class documentation
    for more details.

    The request object may be used as a mapping object, in which case
    values will be looked up in the order: environment variables,
    other variables, form data, and then cookies.
    """

    _hacked_path = None
    args = ()
    _file = None
    _urls = ()

    charset = default_encoding
    retry_max_count = 0

    def supports_retry(self):
        if self.retry_count < self.retry_max_count:
            time.sleep(random.uniform(0, 2 ** (self.retry_count)))
            return 1

    def retry(self):
        self.retry_count = self.retry_count + 1
        self.stdin.seek(0)
        r = self.__class__(stdin=self.stdin,
                           environ=self._orig_env,
                           response=self.response.retry())
        r.retry_count = self.retry_count
        return r

    def clear(self):
        # Clear all references to the input stream, possibly
        # removing tempfiles.
        self.stdin = None
        self._file = None
        self.form.clear()
        self.taintedform.clear()
        # we want to clear the lazy dict here because BaseRequests don't have
        # one.  Without this, there's the possibility of memory leaking
        # after every request.
        self._lazies = {}
        BaseRequest.clear(self)

    def setServerURL(self, protocol=None, hostname=None, port=None):
        """ Set the parts of generated URLs. """
        other = self.other
        server_url = other.get('SERVER_URL', '')
        if protocol is None and hostname is None and port is None:
            return server_url
        old_url = urlparse(server_url)
        if protocol is None:
            protocol = old_url.scheme
        if hostname is None:
            hostname = old_url.hostname
        if port is None:
            port = old_url.port

        if (port is None or default_port[protocol] == port):
            host = hostname
        else:
            host = '{}:{}'.format(hostname, port)
        server_url = other['SERVER_URL'] = '%s://%s' % (protocol, host)
        self._resetURLS()
        return server_url

    def setVirtualRoot(self, path, hard=0):
        """ Treat the current publishing object as a VirtualRoot """
        other = self.other
        if isinstance(path, string_types):
            path = path.split('/')
        self._script[:] = list(map(quote, [_p for _p in path if _p]))
        del self._steps[:]
        parents = other['PARENTS']
        if hard:
            del parents[:-1]
        other['VirtualRootPhysicalPath'] = parents[-1].getPhysicalPath()
        self._resetURLS()

    def getVirtualRoot(self):
        """ Return a slash-separated virtual root.

        If it is same as the physical root, return ''.
        """
        return '/'.join([''] + self._script)

    def physicalPathToVirtualPath(self, path):
        """ Remove the path to the VirtualRoot from a physical path """
        if isinstance(path, string_types):
            path = path.split('/')
        rpp = self.other.get('VirtualRootPhysicalPath', ('',))
        i = 0
        for name in rpp[:len(path)]:
            if path[i] == name:
                i = i + 1
            else:
                break
        return path[i:]

    def physicalPathToURL(self, path, relative=0):
        """ Convert a physical path into a URL in the current context """
        path = self._script + list(
            map(quote, self.physicalPathToVirtualPath(path)))
        if relative:
            path.insert(0, '')
        else:
            path.insert(0, self['SERVER_URL'])
        return '/'.join(path)

    def physicalPathFromURL(self, URL):
        """ Convert a URL into a physical path in the current context.
            If the URL makes no sense in light of the current virtual
            hosting context, a ValueError is raised."""
        other = self.other
        path = [_p for _p in URL.split('/') if _p]

        if URL.find('://') >= 0:
            path = path[2:]

        # Check the path against BASEPATH1
        vhbase = self._script
        vhbl = len(vhbase)
        if path[:vhbl] == vhbase:
            path = path[vhbl:]
        else:
            raise ValueError('Url does not match virtual hosting context')
        vrpp = other.get('VirtualRootPhysicalPath', ('',))
        return list(vrpp) + list(map(unquote, path))

    def _resetURLS(self):
        other = self.other
        other['URL'] = '/'.join(
            [other['SERVER_URL']] + self._script + self._steps)
        for x in self._urls:
            del self.other[x]
        self._urls = ()

    def getClientAddr(self):
        """ The IP address of the client.
        """
        return self._client_addr

    def setupLocale(self):
        envadapter = IUserPreferredLanguages(self, None)
        if envadapter is None:
            self._locale = None
            return

        langs = envadapter.getPreferredLanguages()
        for httplang in langs:
            parts = (httplang.split('-') + [None, None])[:3]
            try:
                self._locale = locales.getLocale(*parts)
                return
            except LoadLocaleError:
                # Just try the next combination
                pass
        else:
            # No combination gave us an existing locale, so use the default,
            # which is guaranteed to exist
            self._locale = locales.getLocale(None, None, None)

    def __init__(self, stdin, environ, response, clean=0):
        self.__doc__ = None  # Make HTTPRequest objects unpublishable
        super(HTTPRequest, self).__init__()
        self._orig_env = environ
        # Avoid the overhead of scrubbing the environment in the
        # case of request cloning for traversal purposes. If the
        # clean flag is set, we know we can use the passed in
        # environ dict directly.
        if not clean:
            environ = sane_environment(environ)

        if 'HTTP_AUTHORIZATION' in environ:
            self._auth = environ['HTTP_AUTHORIZATION']
            response._auth = 1
            del environ['HTTP_AUTHORIZATION']

        self.stdin = stdin
        self.environ = environ
        get_env = environ.get
        self.response = response
        other = self.other = {'RESPONSE': response}
        self.form = {}
        self.taintedform = {}
        self.steps = []
        self._steps = []
        self._lazies = {}
        self._debug = DebugFlags()
        # We don't set up the locale initially but just on first access
        self._locale = _marker

        if 'REMOTE_ADDR' in environ:
            self._client_addr = environ['REMOTE_ADDR']
            if 'HTTP_X_FORWARDED_FOR' in environ and \
               self._client_addr in trusted_proxies:
                # REMOTE_ADDR is one of our trusted local proxies.
                # Not really very remote at all.  The proxy can tell us the
                # IP of the real remote client in the forwarded-for header
                # Skip the proxy-address itself though
                forwarded_for = [
                    e.strip()
                    for e in environ['HTTP_X_FORWARDED_FOR'].split(',')]
                forwarded_for.reverse()
                for entry in forwarded_for:
                    if entry not in trusted_proxies:
                        self._client_addr = entry
                        break
        else:
            self._client_addr = ''

        ################################################################
        # Get base info first. This isn't likely to cause
        # errors and might be useful to error handlers.
        b = script = get_env('SCRIPT_NAME', '').strip()

        # _script and the other _names are meant for URL construction
        self._script = list(map(quote, [_s for _s in script.split('/') if _s]))

        while b and b[-1] == '/':
            b = b[:-1]
        p = b.rfind('/')
        if p >= 0:
            b = b[:p + 1]
        else:
            b = ''
        while b and b[0] == '/':
            b = b[1:]

        server_url = get_env('SERVER_URL', None)
        if server_url is not None:
            other['SERVER_URL'] = server_url = server_url.strip()
        else:
            https_environ = environ.get('HTTPS', False)
            if https_environ and https_environ in ('on', 'ON', '1'):
                protocol = 'https'
            elif environ.get('SERVER_PORT_SECURE', None) == 1:
                protocol = 'https'
            else:
                protocol = 'http'

            if 'HTTP_HOST' in environ:
                host = environ['HTTP_HOST'].strip()
                hostname, port = splitport(host)

                # NOTE: some (DAV) clients manage to forget the port. This
                # can be fixed with the commented code below - the problem
                # is that it causes problems for virtual hosting. I've left
                # the commented code here in case we care enough to come
                # back and do anything with it later.
                #
                # if port is None and 'SERVER_PORT' in environ:
                #     s_port = environ['SERVER_PORT']
                #     if s_port not in ('80', '443'):
                #         port = s_port

            else:
                hostname = environ['SERVER_NAME'].strip()
                port = int(environ['SERVER_PORT'])
            self.setServerURL(protocol=protocol, hostname=hostname, port=port)
            server_url = other['SERVER_URL']

        if server_url[-1:] == '/':
            server_url = server_url[:-1]

        if b:
            self.base = "%s/%s" % (server_url, b)
        else:
            self.base = server_url
        while script[:1] == '/':
            script = script[1:]
        if script:
            script = "%s/%s" % (server_url, script)
        else:
            script = server_url
        other['URL'] = self.script = script
        other['method'] = environ.get('REQUEST_METHOD', 'GET').upper()

        ################################################################
        # Cookie values should *not* be appended to existing form
        # vars with the same name - they are more like default values
        # for names not otherwise specified in the form.
        cookies = {}
        k = get_env('HTTP_COOKIE', '')
        if k:
            parse_cookie(k, cookies)
        self.cookies = cookies
        self.taintedcookies = taint(cookies)

    def processInputs(self):
        """Process request inputs

        See the `Zope Developer Guide Object Publishing chapter
        <https://zope.readthedocs.io/en/latest/zdgbook/ObjectPublishing.html>`_
        for a detailed explanation in the section `Marshalling Arguments from
        the Request`.

        We need to delay input parsing so that it is done under
        publisher control for error handling purposes.
        """
        response = self.response
        environ = self.environ
        method = environ.get('REQUEST_METHOD', 'GET')

        if method != 'GET':
            fp = self.stdin
        else:
            fp = None

        other = self.other

        # If 'QUERY_STRING' is not present in environ
        # FieldStorage will try to get it from sys.argv[1]
        # which is not what we need.
        if 'QUERY_STRING' not in environ:
            environ['QUERY_STRING'] = ''

        meth = None
        fs_kw = {}
        if PY3:
            # In Python 3 we transfrom into a sequence of bytes
            # mapped to `str` via `latin1` decoding.
            # The correct recoding is applied later.
            fs_kw['encoding'] = 'latin1'

        fs = ZopeFieldStorage(
            fp=fp, environ=environ, keep_blank_values=1, **fs_kw)

        # Keep a reference to the FieldStorage. Otherwise it's
        # __del__ method is called too early and closing FieldStorage.file.
        self._hold(fs)

        if not hasattr(fs, 'list') or fs.list is None:
            if 'HTTP_SOAPACTION' in environ:
                # Stash XML request for interpretation by a SOAP-aware view
                other['SOAPXML'] = fs.value
            elif (method == 'POST'
                  and 'text/xml' in fs.headers.get('content-type', '')
                  and use_builtin_xmlrpc(self)):
                # Ye haaa, XML-RPC!
                meth, self.args = xmlrpc.parse_input(fs.value)
                response = xmlrpc.response(response)
                other['RESPONSE'] = self.response = response
                self.maybe_webdav_client = 0
            else:
                self._file = fs.file
        else:
            fslist = fs.list
            params = []
            for item in fslist:
                key = item.name
                if key is None:
                    continue
                if hasattr(item, 'file') and \
                   hasattr(item, 'filename') and \
                   hasattr(item, 'headers'):
                    if item.file and item.filename is not None:
                        item = FileUpload(item)
                    else:
                        item = item.value
                params.append((key, item))
            form, errors = process_parameters(params, self.charset)
            if errors:
                # recopy and clear to break up cycles
                new_errors = errors[:]
                del errors[:]
                # Note: the following introduces a new cycle via `self`
                #  broken in `BaseRequest.traverse` - provided
                #  there is no further exception until after
                #  traversal - or when the request is cleared
                self.post_traverse(self.report_request_parameter_errors,
                                   (new_errors,))
                # make errors available in `other` to
                #  ease the error analysis via `error_log`.
                #  Note: this introduces a cycle via `self` broken
                #    when the request is cleared
                self.other["__request_parameter_errors__"] = new_errors
                del new_errors  # precaution against cycles
            meth = form.pop("__method__", None)
            if isinstance(meth, list):  # backward compatibility
                meth = meth[-1]
            self.form.update(form)
            self.taintedform.update(taint(form))

        if meth:
            if 'PATH_INFO' in environ:
                path = environ['PATH_INFO']
                while path[-1:] == '/':
                    path = path[:-1]
            else:
                path = ''
            other['PATH_INFO'] = "%s/%s" % (path, meth)
            self._hacked_path = 1

    def postProcessInputs(self):
        """Process the values in request.form to decode strings to unicode.
        """
        for name, value in self.form.items():
            self.form[name] = _decode(value, default_encoding)

    def resolve_url(self, url):
        # Attempt to resolve a url into an object in the Zope
        # namespace. The url must be a fully-qualified url. The
        # method will return the requested object if it is found
        # or raise the same HTTP error that would be raised in
        # the case of a real web request. If the passed in url
        # does not appear to describe an object in the system
        # namespace (e.g. the host, port or script name don't
        # match that of the current request), a ValueError will
        # be raised.
        if url.find(self.script) != 0:
            raise ValueError('Different namespace.')
        path = url[len(self.script):]
        while path and path[0] == '/':
            path = path[1:]
        while path and path[-1] == '/':
            path = path[:-1]
        req = self.clone()
        rsp = req.response
        req['PATH_INFO'] = path
        object = None

        # Try to traverse to get an object. Note that we call
        # the exception method on the response, but we don't
        # want to actually abort the current transaction
        # (which is usually the default when the exception
        # method is called on the response).
        try:
            object = req.traverse(path)
        except Exception as exc:
            rsp.exception()
            req.clear()
            raise exc.__class__(rsp.errmsg)

        # The traversal machinery may return a "default object"
        # like an index_html document. This is not appropriate
        # in the context of the resolve_url method so we need
        # to ensure we are getting the actual object named by
        # the given url, and not some kind of default object.
        if hasattr(object, 'id'):
            if callable(object.id):
                name = object.id()
            else:
                name = object.id
        elif hasattr(object, '__name__'):
            name = object.__name__
        else:
            name = ''
        if name != os.path.split(path)[-1]:
            object = req.PARENTS[0]

        req.clear()
        return object

    def clone(self):
        # Return a clone of the current request object
        # that may be used to perform object traversal.
        environ = self.environ.copy()
        environ['REQUEST_METHOD'] = 'GET'
        if self._auth:
            environ['HTTP_AUTHORIZATION'] = self._auth
        if self.response is not None:
            response = self.response.__class__()
        else:
            response = None
        clone = self.__class__(None, environ, response, clean=1)
        clone['PARENTS'] = [self['PARENTS'][-1]]
        directlyProvides(clone, *directlyProvidedBy(self))
        return clone

    def getHeader(self, name, default=None, literal=False):
        """Return the named HTTP header, or an optional default
        argument or None if the header is not found. Note that
        both original and CGI-ified header names are recognized,
        e.g. 'Content-Type', 'CONTENT_TYPE' and 'HTTP_CONTENT_TYPE'
        should all return the Content-Type header, if available.
        """
        environ = self.environ
        if not literal:
            name = name.replace('-', '_').upper()
        val = environ.get(name, None)
        if val is not None:
            return val
        if name[:5] != 'HTTP_':
            name = 'HTTP_%s' % name
        return environ.get(name, default)

    get_header = getHeader  # BBB

    def get(self, key, default=None, returnTaints=0,
            URLmatch=re.compile('URL(PATH)?([0-9]+)$').match,
            BASEmatch=re.compile('BASE(PATH)?([0-9]+)$').match,
            ):
        """Get a variable value

        Return a value for the variable key, or default if not found.

        If key is "REQUEST", return the request.
        Otherwise, the value will be looked up from one of the request data
        categories. The search order is:
        other (the target for explicitly set variables),
        the special URL and BASE variables,
        environment variables,
        common variables (defined by the request class),
        lazy variables (set with set_lazy),
        form data and cookies.

        If returnTaints has a true value, then the access to
        form and cookie variables returns values with special
        protection against embedded HTML fragments to counter
        some cross site scripting attacks.
        """

        if key == 'REQUEST':
            return self

        other = self.other
        if key in other:
            return other[key]

        if key[:1] == 'U':
            match = URLmatch(key)
            if match is not None:
                pathonly, n = match.groups()
                path = self._script + self._steps
                n = len(path) - int(n)
                if n < 0:
                    raise KeyError(key)
                if pathonly:
                    path = [''] + path[:n]
                else:
                    path = [other['SERVER_URL']] + path[:n]
                URL = '/'.join(path)
                if 'PUBLISHED' in other:
                    # Don't cache URLs until publishing traversal is done.
                    other[key] = URL
                    self._urls = self._urls + (key,)
                return URL

        if key in isCGI_NAMEs or key[:5] == 'HTTP_':
            environ = self.environ
            if key in environ and (key not in hide_key):
                return environ[key]
            return ''

        if key[:1] == 'B':
            match = BASEmatch(key)
            if match is not None:
                pathonly, n = match.groups()
                path = self._steps
                n = int(n)
                if n:
                    n = n - 1
                    if len(path) < n:
                        raise KeyError(key)

                    v = self._script + path[:n]
                else:
                    v = self._script[:-1]
                if pathonly:
                    v.insert(0, '')
                else:
                    v.insert(0, other['SERVER_URL'])
                URL = '/'.join(v)
                if 'PUBLISHED' in other:
                    # Don't cache URLs until publishing traversal is done.
                    other[key] = URL
                    self._urls = self._urls + (key,)
                return URL

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

        v = self.common.get(key, _marker)
        if v is not _marker:
            return v

        if self._lazies:
            v = self._lazies.get(key, _marker)
            if v is not _marker:
                if callable(v):
                    v = v()
                self[key] = v  # Promote lazy value
                del self._lazies[key]
                return v

        # Return tainted data first (marked as suspect)
        if returnTaints:
            v = self.taintedform.get(key, _marker)
            if v is not _marker:
                return v

        # Untrusted data *after* trusted data
        v = self.form.get(key, _marker)
        if v is not _marker:
            return v

        # Return tainted data first (marked as suspect)
        if returnTaints:
            v = self.taintedcookies.get(key, _marker)
            if v is not _marker:
                return v

        # Untrusted data *after* trusted data
        v = self.cookies.get(key, _marker)
        if v is not _marker:
            return v

        return default

    def __getitem__(self, key, default=_marker, returnTaints=0):
        v = self.get(key, default, returnTaints=returnTaints)
        if v is _marker:
            raise KeyError(key)
        return v

    # Using the getattr protocol to retrieve form values and similar
    # is discouraged and is likely to be deprecated in the future.
    # request.get(key) or request[key] should be used instead
    def __getattr__(self, key, default=_marker, returnTaints=0):
        v = self.get(key, default, returnTaints=returnTaints)
        if v is _marker:
            if key == 'locale':
                # we only create the _locale on first access, as setting it
                # up might be slow and we don't want to slow down every
                # request
                if self._locale is _marker:
                    self.setupLocale()
                return self._locale
            if key == 'debug':
                return self._debug
            raise AttributeError(key)
        return v

    def set_lazy(self, key, callable):
        self._lazies[key] = callable

    def __contains__(self, key, returnTaints=0):
        return self.has_key(key, returnTaints=returnTaints)  # NOQA

    def has_key(self, key, returnTaints=0):
        try:
            self.__getitem__(key, returnTaints=returnTaints)
        except Exception:
            return 0
        else:
            return 1

    def keys(self, returnTaints=0):
        keys = {}
        keys.update(self.common)
        keys.update(self._lazies)

        for key in self.environ.keys():
            if (key in isCGI_NAMEs or key[:5] == 'HTTP_') and \
               (key not in hide_key):
                keys[key] = 1

        # Cache URLN and BASEN in self.other.
        # This relies on a side effect of has_key.
        n = 0
        while 1:
            n = n + 1
            key = "URL%s" % n
            if key not in self:  # NOQA
                break

        n = 0
        while 1:
            n = n + 1
            key = "BASE%s" % n
            if key not in self:  # NOQA
                break

        keys.update(self.other)
        keys.update(self.cookies)
        if returnTaints:
            keys.update(self.taintedcookies)
        keys.update(self.form)
        if returnTaints:
            keys.update(self.taintedform)

        keys = list(keys.keys())
        keys.sort()

        return keys

    def __str__(self):
        result = "<h3>form</h3><table>"
        row = '<tr valign="top" align="left"><th>%s</th><td>%s</td></tr>'
        for k, v in _filterPasswordFields(self.form.items()):
            result = result + row % (escape(k, False), escape(repr(v), False))
        result = result + "</table><h3>cookies</h3><table>"
        for k, v in _filterPasswordFields(self.cookies.items()):
            result = result + row % (escape(k, False), escape(repr(v), False))
        result = result + "</table><h3>lazy items</h3><table>"
        for k, v in _filterPasswordFields(self._lazies.items()):
            result = result + row % (escape(k, False), escape(repr(v), False))
        result = result + "</table><h3>other</h3><table>"
        for k, v in _filterPasswordFields(self.other.items()):
            if k in ('PARENTS', 'RESPONSE'):
                continue
            result = result + row % (escape(k, False), escape(repr(v), False))

        for n in "0123456789":
            key = "URL%s" % n
            try:
                result = result + row % (key, escape(self[key], False))
            except KeyError:
                pass
        for n in "0123456789":
            key = "BASE%s" % n
            try:
                result = result + row % (key, escape(self[key], False))
            except KeyError:
                pass

        result = result + "</table><h3>environ</h3><table>"
        for k, v in self.environ.items():
            if k not in hide_key:
                result = result + row % (
                    escape(k, False), escape(repr(v), False))
        return result + "</table>"

    def __repr__(self):
        return "<%s, URL=%s>" % (self.__class__.__name__, self.get('URL'))

    def text(self):
        result = "FORM\n\n"
        row = '%-20s %s\n'
        for k, v in _filterPasswordFields(self.form.items()):
            result = result + row % (k, repr(v))
        result = result + "\nCOOKIES\n\n"
        for k, v in _filterPasswordFields(self.cookies.items()):
            result = result + row % (k, repr(v))
        result = result + "\nLAZY ITEMS\n\n"
        for k, v in _filterPasswordFields(self._lazies.items()):
            result = result + row % (k, repr(v))
        result = result + "\nOTHER\n\n"
        for k, v in _filterPasswordFields(self.other.items()):
            if k in ('PARENTS', 'RESPONSE'):
                continue
            result = result + row % (k, repr(v))

        for n in "0123456789":
            key = "URL%s" % n
            try:
                result = result + row % (key, self[key])
            except KeyError:
                pass
        for n in "0123456789":
            key = "BASE%s" % n
            try:
                result = result + row % (key, self[key])
            except KeyError:
                pass

        result = result + "\nENVIRON\n\n"
        for k, v in self.environ.items():
            if k not in hide_key:
                result = result + row % (k, v)
        return result

    def _authUserPW(self):
        # Can return None
        return basic_auth_decode(self._auth)

    def taintWrapper(self, enabled=TAINTING_ENABLED):
        return enabled and TaintRequestWrapper(self) or self

    # Original version: zope.publisher.http.HTTPRequest.shiftNameToApplication
    def shiftNameToApplication(self):
        """see zope.publisher.interfaces.http.IVirtualHostRequest"""
        if len(self._steps) == 1:
            self._script.append(self._steps.pop())
            self._resetURLS()
            return

        raise ValueError("Can only shift leading traversal "
                         "names to application names")

    def getURL(self):
        return self.URL

    def report_request_parameter_errors(self, errors):
        """raise ``RequestParameterError(errors)``

        Used as "post_traverse" to delay error reports
        for request parameter processing to ensure that
        the application specific error handling is available.
        """
        if errors:
            exc = RequestParameterError(errors)
            if PY3:
                exc.__cause__ = errors[0][2][1]
            reraise(exc.__class__, exc, errors[0][2][2])


class WSGIRequest(HTTPRequest):
    # A request object for WSGI, no docstring to avoid being publishable.
    pass


class TaintRequestWrapper(object):

    def __init__(self, req):
        self._req = req

    def __contains__(self, *args, **kw):
        return TaintMethodWrapper(self._req.__contains__)(*args, **kw)

    def __getattr__(self, key, *args, **kw):
        if key not in self._req.keys():
            item = getattr(self._req, key, _marker)
            if item is not _marker:
                return item
        return TaintMethodWrapper(self._req.__getattr__)(key, *args, **kw)

    def __getitem__(self, *args, **kw):
        return TaintMethodWrapper(self._req.__getitem__)(*args, **kw)

    def __len__(self):
        return len(self._req)

    def get(self, *args, **kw):
        return TaintMethodWrapper(self._req.get)(*args, **kw)

    def has_key(self, *args, **kw):
        return TaintMethodWrapper(self._req.has_key)(*args, **kw)

    def keys(self, *args, **kw):
        return TaintMethodWrapper(self._req.keys)(*args, **kw)


class TaintMethodWrapper(object):

    def __init__(self, method):
        self._method = method

    def __call__(self, *args, **kw):
        kw['returnTaints'] = 1
        return self._method(*args, **kw)


def has_codec(x):
    try:
        codecs.lookup(x)
    except (LookupError, SystemError):
        return 0
    else:
        return 1


def sane_environment(env):
    # return an environment mapping which has been cleaned of
    # funny business such as REDIRECT_ prefixes added by Apache
    # or HTTP_CGI_AUTHORIZATION hacks.
    dict = {}
    for key, val in env.items():
        while key[:9] == 'REDIRECT_':
            key = key[9:]
        dict[key] = val
    if 'HTTP_CGI_AUTHORIZATION' in dict:
        dict['HTTP_AUTHORIZATION'] = dict['HTTP_CGI_AUTHORIZATION']
        try:
            del dict['HTTP_CGI_AUTHORIZATION']
        except Exception:
            pass
    return dict


class ZopeFieldStorage(FieldStorage):
    """This subclass exists to work around a Python bug
    (see https://bugs.python.org/issue27777) to make sure
    we can read binary data from a request body.
    """

    def read_binary(self):
        self._binary_file = True
        return FieldStorage.read_binary(self)


# Original version: zope.publisher.browser.FileUpload
class FileUpload(object):
    '''File upload objects

    File upload objects are used to represent file-uploaded data.

    File upload objects can be used just like files.

    In addition, they have a 'headers' attribute that is a dictionary
    containing the file-upload headers, and a 'filename' attribute
    containing the name of the uploaded file.
    The attributes 'type' (``str``) and 'type_options'
    (``dict``) contain the
    content type and content type options, respectively -
    from a 'content-type' header; if there is no such header
    'type' is ``None``.
    '''

    # Allow access to attributes such as headers and filename so
    # that protected code can use DTML to work with FileUploads.
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, aFieldStorage):
        self.file = aFieldStorage.file
        self.headers = aFieldStorage.headers
        self.filename = aFieldStorage.filename
        self.name = aFieldStorage.name
        self.type = aFieldStorage.type
        self.type_options = aFieldStorage.type_options

        # Add an assertion to the rfc822.Message object that implements
        # self.headers so that managed code can access them.
        try:
            self.headers.__allow_access_to_unprotected_subobjects__ = 1
        except Exception:
            pass

    def __getattribute__(self, key):
        if key in ('close', 'closed', 'detach', 'fileno', 'flush',
                   'getbuffer', 'getvalue', 'isatty', 'read', 'read1',
                   'readable', 'readinto', 'readline', 'readlines',
                   'seek', 'seekable', 'tell', 'truncate', 'writable',
                   'write', 'writelines', 'name'):
            file = object.__getattribute__(self, 'file')
            func = getattr(file, key, _marker)
            if func is not _marker:
                return func
        # Always fall back to looking things up on self
        return object.__getattribute__(self, key)

    def __iter__(self):
        return self.file.__iter__()

    def __bool__(self):
        """FileUpload objects are considered false if their
           filename is empty.
        """
        return bool(self.filename)

    def __next__(self):
        return self.file.__next__()

    if PY2:
        def __nonzero__(self):
            return self.__bool__()

        def next(self):
            return self.file.next()

        def xreadlines(self):
            return self


QPARMRE = re.compile(
    '([\x00- ]*([^\x00- ;,="]+)="([^"]*)"([\x00- ]*[;,])?[\x00- ]*)')
PARMRE = re.compile(
    '([\x00- ]*([^\x00- ;,="]+)=([^;]*)([\x00- ]*[;,])?[\x00- ]*)')
PARAMLESSRE = re.compile(
    '([\x00- ]*([^\x00- ;,="]+)[\x00- ]*[;,][\x00- ]*)')


def parse_cookie(text,
                 result=None,
                 qparmre=QPARMRE,
                 parmre=PARMRE,
                 paramlessre=PARAMLESSRE,
                 ):

    if result is None:
        result = {}

    mo_q = qparmre.match(text)

    if mo_q:
        # Match quoted correct cookies
        c_len = len(mo_q.group(1))
        name = mo_q.group(2)
        value = mo_q.group(3)

    else:
        # Match evil MSIE cookies ;)
        mo_p = parmre.match(text)

        if mo_p:
            c_len = len(mo_p.group(1))
            name = mo_p.group(2)
            value = mo_p.group(3)
        else:
            # Broken Cookie without = nor value.
            broken_p = paramlessre.match(text)
            if broken_p:
                c_len = len(broken_p.group(1))
                name = broken_p.group(2)
                value = ''
            else:
                return result

    if name not in result:
        result[name] = unquote(value)

    return parse_cookie(text[c_len:], result)


class record(object):

    # Allow access to record methods and values from DTML
    __allow_access_to_unprotected_subobjects__ = 1
    _guarded_writes = 1

    def __init__(self, **kw):
        for k in kw:
            setattr(self, k, kw[k])

    def __getattr__(self, key, default=None):
        if key in ('get',
                   'keys',
                   'items',
                   'values',
                   'copy'):
            return getattr(self.__dict__, key)
        raise AttributeError(key)

    def __contains__(self, key):
        return key in self.__dict__

    def __getitem__(self, key):
        return self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        return ", ".join("%s: %s" % item for item in
                         sorted(self.__dict__.items()))

    def __repr__(self):
        # return repr( self.__dict__ )
        return '{%s}' % ', '.join(
            "'%s': %s" % (item[0], repr(item[1])) for item in
            sorted(self.__dict__.items()))

    def __eq__(self, other):
        if not isinstance(other, record):
            return False
        return sorted(self.__dict__.items()) == sorted(other.__dict__.items())


def _filterPasswordFields(items):
    # Collector #777:  filter out request fields which contain 'passw'

    result = []

    for k, v in items:

        if 'passw' in k.lower():
            v = '<password obscured>'

        result.append((k, v))

    return result


def _decode(value, charset):
    """Recursively look for string values and decode.
    """
    if isinstance(value, list):
        return [_decode(v, charset) for v in value]
    elif isinstance(value, tuple):
        return tuple(_decode(v, charset) for v in value)
    elif isinstance(value, dict):
        return dict((k, _decode(v, charset)) for k, v in value.items())
    elif isinstance(value, binary_type):
        return text_type(value, charset, 'replace')
    return value


def use_builtin_xmlrpc(request):
    checker = queryUtility(IXmlrpcChecker)
    return checker is None or checker(request)


def taint(d):
    """return as ``dict`` the items from *d* which require tainting.

    *d* must be a ``dict`` with ``str`` keys and values recursively
    build from elementary values, ``list``, ``tuple`` and ``record``.
    """
    def should_taint(v):
        """check whether *v* needs tainting."""
        if isinstance(v, (list, tuple)):
            return any(should_taint(x) for x in v)
        if isinstance(v, record):
            for k in v:
                if should_taint(k):
                    return True
                if should_taint(v[k]):
                    return True
        return should_be_tainted(v)

    def _taint(v):
        """return a copy of *v* with tainted replacements.

        In the copy, each ``str`` which requires tainting
        is replaced by the corresponding ``taint_string``.
        """
        __traceback_info__ = v
        if isinstance(v, string_types) and should_be_tainted(v):
            return taint_string(v)
        if isinstance(v, (list, tuple)):
            return v.__class__(_taint(x) for x in v)
        if isinstance(v, record):
            rn = record()
            for k in v:
                __traceback_info__ = v, k
                if should_be_tainted(k):
                    raise ValueError("Cannot taint `record` attribute names")
                setattr(rn, k, _taint(v[k]))
            return rn
        return v
    td = {}
    for k in d:
        v = d[k]
        if should_taint(k) or should_taint(v):
            td[_taint(k)] = _taint(v)
    return td


def should_be_tainted(v):
    """Work around ``AccessControl`` weakness."""
    if isinstance(v, FileUpload):
        # `base_should_be_tainted` would read `v` as a side effect
        return False
    try:
        return base_should_be_tainted(v)
    except Exception:
        return False


from .request_params import process_parameters  # noqa: 
