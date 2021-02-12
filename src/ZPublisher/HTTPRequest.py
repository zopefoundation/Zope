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
import html
import os
import random
import re
import time
from cgi import FieldStorage
from copy import deepcopy
from urllib.parse import unquote
from urllib.parse import urlparse

from AccessControl.tainted import should_be_tainted
from AccessControl.tainted import taint_string
from zope.component import queryUtility
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.locales import LoadLocaleError
from zope.i18n.locales import locales
from zope.interface import directlyProvidedBy
from zope.interface import directlyProvides
from zope.interface import implementer
from zope.publisher.base import DebugFlags
from zope.publisher.http import splitport
from zope.publisher.interfaces.browser import IBrowserRequest
from ZPublisher import xmlrpc
from ZPublisher.BaseRequest import BaseRequest
from ZPublisher.BaseRequest import quote
from ZPublisher.Converters import get_converter
from ZPublisher.interfaces import IXmlrpcChecker
from ZPublisher.utils import basic_auth_decode


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

search_type = re.compile(r'(:[a-zA-Z][-a-zA-Z0-9_]+|\.[xy])$').search

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
        return self.retry_count < self.retry_max_count

    def delay_retry(self):
        # Insert a delay before retrying. Moved here from supports_retry.
        time.sleep(random.uniform(0, 2 ** (self.retry_count)))

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
            host = f'{hostname}:{port}'
        server_url = other['SERVER_URL'] = f'{protocol}://{host}'
        self._resetURLS()
        return server_url

    def setVirtualRoot(self, path, hard=0):
        """ Treat the current publishing object as a VirtualRoot """
        other = self.other
        if isinstance(path, str):
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
        if isinstance(path, str):
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
            elif (environ.get('REQUEST_SCHEME', '') or '').lower() == 'https':
                protocol = 'https'
            elif environ.get('wsgi.url_scheme') == 'https':
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
            self.base = f"{server_url}/{b}"
        else:
            self.base = server_url
        while script[:1] == '/':
            script = script[1:]
        if script:
            script = f"{server_url}/{script}"
        else:
            script = server_url
        other['URL'] = self.script = script
        other['method'] = environ.get('REQUEST_METHOD', 'GET').upper()

        # Make WEBDAV_SOURCE_PORT reachable with a simple REQUEST.get
        # to stay backwards-compatible
        if environ.get('WEBDAV_SOURCE_PORT'):
            other['WEBDAV_SOURCE_PORT'] = environ.get('WEBDAV_SOURCE_PORT')

        ################################################################
        # Cookie values should *not* be appended to existing form
        # vars with the same name - they are more like default values
        # for names not otherwise specified in the form.
        cookies = {}
        taintedcookies = {}
        k = get_env('HTTP_COOKIE', '')
        if k:
            parse_cookie(k, cookies)
            for k, v in cookies.items():
                istainted = 0
                if should_be_tainted(k):
                    k = taint_string(k)
                    istainted = 1
                if should_be_tainted(v):
                    v = taint_string(v)
                    istainted = 1
                if istainted:
                    taintedcookies[k] = v
        self.cookies = cookies
        self.taintedcookies = taintedcookies

    def processInputs(
            self,
            # "static" variables that we want to be local for speed
            SEQUENCE=1,
            DEFAULT=2,
            RECORD=4,
            RECORDS=8,
            REC=12,  # RECORD | RECORDS
            EMPTY=16,
            CONVERTED=32,
            hasattr=hasattr,
            getattr=getattr,
            setattr=setattr):
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

        form = self.form
        other = self.other
        taintedform = self.taintedform

        # If 'QUERY_STRING' is not present in environ
        # FieldStorage will try to get it from sys.argv[1]
        # which is not what we need.
        if 'QUERY_STRING' not in environ:
            environ['QUERY_STRING'] = ''

        meth = None
        fs_kw = {}
        fs_kw['encoding'] = self.charset

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
            tuple_items = {}
            defaults = {}
            tainteddefaults = {}
            converter = None

            for item in fslist:

                isFileUpload = 0
                key = item.name
                if key is None:
                    continue

                if hasattr(item, 'file') and \
                   hasattr(item, 'filename') and \
                   hasattr(item, 'headers'):
                    if item.file and item.filename is not None:
                        item = FileUpload(item)
                        isFileUpload = 1
                    else:
                        item = item.value

                flags = 0
                character_encoding = ''
                # Variables for potentially unsafe values.
                tainted = None
                converter_type = None

                # Loop through the different types and set
                # the appropriate flags

                # We'll search from the back to the front.
                # We'll do the search in two steps.  First, we'll
                # do a string search, and then we'll check it with
                # a re search.

                delim = key.rfind(':')
                if delim >= 0:
                    mo = search_type(key, delim)
                    if mo:
                        delim = mo.start(0)
                    else:
                        delim = -1

                    while delim >= 0:
                        type_name = key[delim + 1:]
                        key = key[:delim]
                        c = get_converter(type_name, None)

                        if c is not None:
                            converter = c
                            converter_type = type_name
                            flags = flags | CONVERTED
                        elif type_name == 'list':
                            flags = flags | SEQUENCE
                        elif type_name == 'tuple':
                            tuple_items[key] = 1
                            flags = flags | SEQUENCE
                        elif type_name == 'method' or type_name == 'action':
                            if delim:
                                meth = key
                            else:
                                meth = item
                        elif (type_name == 'default_method'
                              or type_name == 'default_action'):
                            if not meth:
                                if delim:
                                    meth = key
                                else:
                                    meth = item
                        elif type_name == 'default':
                            flags = flags | DEFAULT
                        elif type_name == 'record':
                            flags = flags | RECORD
                        elif type_name == 'records':
                            flags = flags | RECORDS
                        elif type_name == 'ignore_empty':
                            if not item:
                                flags = flags | EMPTY
                        elif has_codec(type_name):
                            character_encoding = type_name

                        delim = key.rfind(':')
                        if delim < 0:
                            break
                        mo = search_type(key, delim)
                        if mo:
                            delim = mo.start(0)
                        else:
                            delim = -1

                # Filter out special names from form:
                if key in isCGI_NAMEs or key.startswith('HTTP_'):
                    continue

                # If the key is tainted, mark it so as well.
                tainted_key = key
                if should_be_tainted(key):
                    tainted_key = taint_string(key)

                if flags:

                    # skip over empty fields
                    if flags & EMPTY:
                        continue

                    # Split the key and its attribute
                    if flags & REC:
                        key = key.split(".")
                        key, attr = ".".join(key[:-1]), key[-1]

                        # Update the tainted_key if necessary
                        tainted_key = key
                        if should_be_tainted(key):
                            tainted_key = taint_string(key)

                        # Attributes cannot hold a <.
                        if should_be_tainted(attr):
                            raise ValueError(
                                "%s is not a valid record attribute name" %
                                html.escape(attr, True))

                    # defer conversion
                    if flags & CONVERTED:
                        try:
                            if character_encoding:
                                # We have a string with a specified character
                                # encoding.  This gets passed to the converter
                                # either as unicode, if it can handle it, or
                                # crunched back down to utf-8 if it can not.
                                if isinstance(item, bytes):
                                    item = str(item, character_encoding)
                                if hasattr(converter, 'convert_unicode'):
                                    item = converter.convert_unicode(item)
                                else:
                                    item = converter(
                                        item.encode(default_encoding))
                            else:
                                item = converter(item)

                            # Flag potentially unsafe values
                            if converter_type in ('string', 'required', 'text',
                                                  'ustring', 'utext'):
                                if not isFileUpload and \
                                   should_be_tainted(item):
                                    tainted = taint_string(item)
                            elif converter_type in ('tokens', 'lines',
                                                    'utokens', 'ulines'):
                                is_tainted = 0
                                tainted = item[:]
                                for i in range(len(tainted)):
                                    if should_be_tainted(tainted[i]):
                                        is_tainted = 1
                                        tainted[i] = taint_string(tainted[i])
                                if not is_tainted:
                                    tainted = None

                        except Exception:
                            if not item and \
                               not (flags & DEFAULT) and \
                               key in defaults:
                                item = defaults[key]
                                if flags & RECORD:
                                    item = getattr(item, attr)
                                if flags & RECORDS:
                                    item = getattr(item[-1], attr)
                                if tainted_key in tainteddefaults:
                                    tainted = tainteddefaults[tainted_key]
                                    if flags & RECORD:
                                        tainted = getattr(tainted, attr)
                                    if flags & RECORDS:
                                        tainted = getattr(tainted[-1], attr)
                            else:
                                raise

                    elif not isFileUpload and should_be_tainted(item):
                        # Flag potentially unsafe values
                        tainted = taint_string(item)

                    # If the key is tainted, we need to store stuff in the
                    # tainted dict as well, even if the value is safe.
                    if should_be_tainted(tainted_key) and tainted is None:
                        tainted = item

                    # Determine which dictionary to use
                    if flags & DEFAULT:
                        mapping_object = defaults
                        tainted_mapping = tainteddefaults
                    else:
                        mapping_object = form
                        tainted_mapping = taintedform

                    # Insert in dictionary
                    if key in mapping_object:
                        if flags & RECORDS:
                            # Get the list and the last record
                            # in the list. reclist is mutable.
                            reclist = mapping_object[key]
                            x = reclist[-1]

                            if tainted:
                                # Store a tainted copy as well
                                if tainted_key not in tainted_mapping:
                                    tainted_mapping[tainted_key] = deepcopy(
                                        reclist)
                                treclist = tainted_mapping[tainted_key]
                                lastrecord = treclist[-1]

                                if not hasattr(lastrecord, attr):
                                    if flags & SEQUENCE:
                                        tainted = [tainted]
                                    setattr(lastrecord, attr, tainted)
                                else:
                                    if flags & SEQUENCE:
                                        getattr(
                                            lastrecord, attr).append(tainted)
                                    else:
                                        newrec = record()
                                        setattr(newrec, attr, tainted)
                                        treclist.append(newrec)

                            elif tainted_key in tainted_mapping:
                                # If we already put a tainted value into this
                                # recordset, we need to make sure the whole
                                # recordset is built.
                                treclist = tainted_mapping[tainted_key]
                                lastrecord = treclist[-1]
                                copyitem = item

                                if not hasattr(lastrecord, attr):
                                    if flags & SEQUENCE:
                                        copyitem = [copyitem]
                                    setattr(lastrecord, attr, copyitem)
                                else:
                                    if flags & SEQUENCE:
                                        getattr(
                                            lastrecord, attr).append(copyitem)
                                    else:
                                        newrec = record()
                                        setattr(newrec, attr, copyitem)
                                        treclist.append(newrec)

                            if not hasattr(x, attr):
                                # If the attribute does not
                                # exist, set it
                                if flags & SEQUENCE:
                                    item = [item]
                                setattr(x, attr, item)
                            else:
                                if flags & SEQUENCE:
                                    # If the attribute is a
                                    # sequence, append the item
                                    # to the existing attribute
                                    y = getattr(x, attr)
                                    y.append(item)
                                    setattr(x, attr, y)
                                else:
                                    # Create a new record and add
                                    # it to the list
                                    n = record()
                                    setattr(n, attr, item)
                                    mapping_object[key].append(n)
                        elif flags & RECORD:
                            b = mapping_object[key]
                            if flags & SEQUENCE:
                                item = [item]
                                if not hasattr(b, attr):
                                    # if it does not have the
                                    # attribute, set it
                                    setattr(b, attr, item)
                                else:
                                    # it has the attribute so
                                    # append the item to it
                                    setattr(b, attr, getattr(b, attr) + item)
                            else:
                                # it is not a sequence so
                                # set the attribute
                                setattr(b, attr, item)

                            # Store a tainted copy as well if necessary
                            if tainted:
                                if tainted_key not in tainted_mapping:
                                    tainted_mapping[tainted_key] = deepcopy(
                                        mapping_object[key])
                                b = tainted_mapping[tainted_key]
                                if flags & SEQUENCE:
                                    seq = getattr(b, attr, [])
                                    seq.append(tainted)
                                    setattr(b, attr, seq)
                                else:
                                    setattr(b, attr, tainted)

                            elif tainted_key in tainted_mapping:
                                # If we already put a tainted value into this
                                # record, we need to make sure the whole record
                                # is built.
                                b = tainted_mapping[tainted_key]
                                if flags & SEQUENCE:
                                    seq = getattr(b, attr, [])
                                    seq.append(item)
                                    setattr(b, attr, seq)
                                else:
                                    setattr(b, attr, item)

                        else:
                            # it is not a record or list of records
                            found = mapping_object[key]

                            if tainted:
                                # Store a tainted version if necessary
                                if tainted_key not in tainted_mapping:
                                    copied = deepcopy(found)
                                    if isinstance(copied, list):
                                        tainted_mapping[tainted_key] = copied
                                    else:
                                        tainted_mapping[tainted_key] = [copied]
                                tainted_mapping[tainted_key].append(tainted)

                            elif tainted_key in tainted_mapping:
                                # We may already have encountered a tainted
                                # value for this key, and the tainted_mapping
                                # needs to hold all the values.
                                tfound = tainted_mapping[tainted_key]
                                if isinstance(tfound, list):
                                    tainted_mapping[tainted_key].append(item)
                                else:
                                    tainted_mapping[tainted_key] = [tfound,
                                                                    item]

                            if isinstance(found, list):
                                found.append(item)
                            else:
                                found = [found, item]
                                mapping_object[key] = found
                    else:
                        # The dictionary does not have the key
                        if flags & RECORDS:
                            # Create a new record, set its attribute
                            # and put it in the dictionary as a list
                            a = record()
                            if flags & SEQUENCE:
                                item = [item]
                            setattr(a, attr, item)
                            mapping_object[key] = [a]

                            if tainted:
                                # Store a tainted copy if necessary
                                a = record()
                                if flags & SEQUENCE:
                                    tainted = [tainted]
                                setattr(a, attr, tainted)
                                tainted_mapping[tainted_key] = [a]

                        elif flags & RECORD:
                            # Create a new record, set its attribute
                            # and put it in the dictionary
                            if flags & SEQUENCE:
                                item = [item]
                            r = mapping_object[key] = record()
                            setattr(r, attr, item)

                            if tainted:
                                # Store a tainted copy if necessary
                                if flags & SEQUENCE:
                                    tainted = [tainted]
                                r = tainted_mapping[tainted_key] = record()
                                setattr(r, attr, tainted)
                        else:
                            # it is not a record or list of records
                            if flags & SEQUENCE:
                                item = [item]
                            mapping_object[key] = item

                            if tainted:
                                # Store a tainted copy if necessary
                                if flags & SEQUENCE:
                                    tainted = [tainted]
                                tainted_mapping[tainted_key] = tainted

                else:
                    # This branch is for case when no type was specified.
                    mapping_object = form

                    if not isFileUpload and should_be_tainted(item):
                        tainted = taint_string(item)
                    elif should_be_tainted(key):
                        tainted = item

                    # Insert in dictionary
                    if key in mapping_object:
                        # it is not a record or list of records
                        found = mapping_object[key]

                        if tainted:
                            # Store a tainted version if necessary
                            if tainted_key not in taintedform:
                                copied = deepcopy(found)
                                if isinstance(copied, list):
                                    taintedform[tainted_key] = copied
                                else:
                                    taintedform[tainted_key] = [copied]
                            elif not isinstance(
                                    taintedform[tainted_key], list):
                                taintedform[tainted_key] = [
                                    taintedform[tainted_key]]
                            taintedform[tainted_key].append(tainted)

                        elif tainted_key in taintedform:
                            # We may already have encountered a tainted value
                            # for this key, and the taintedform needs to hold
                            # all the values.
                            tfound = taintedform[tainted_key]
                            if isinstance(tfound, list):
                                taintedform[tainted_key].append(item)
                            else:
                                taintedform[tainted_key] = [tfound, item]

                        if isinstance(found, list):
                            found.append(item)
                        else:
                            found = [found, item]
                            mapping_object[key] = found
                    else:
                        mapping_object[key] = item
                        if tainted:
                            taintedform[tainted_key] = tainted

            # insert defaults into form dictionary
            if defaults:
                for key, value in defaults.items():
                    tainted_key = key
                    if should_be_tainted(key):
                        tainted_key = taint_string(key)

                    if key not in form:
                        # if the form does not have the key,
                        # set the default
                        form[key] = value

                        if tainted_key in tainteddefaults:
                            taintedform[tainted_key] = \
                                tainteddefaults[tainted_key]
                    else:
                        # The form has the key
                        tdefault = tainteddefaults.get(tainted_key, value)
                        if isinstance(value, record):
                            # if the key is mapped to a record, get the
                            # record
                            r = form[key]

                            # First deal with tainted defaults.
                            if tainted_key in taintedform:
                                tainted = taintedform[tainted_key]
                                for k, v in tdefault.__dict__.items():
                                    if not hasattr(tainted, k):
                                        setattr(tainted, k, v)

                            elif tainted_key in tainteddefaults:
                                # Find out if any of the tainted default
                                # attributes needs to be copied over.
                                missesdefault = 0
                                for k, v in tdefault.__dict__.items():
                                    if not hasattr(r, k):
                                        missesdefault = 1
                                        break
                                if missesdefault:
                                    tainted = deepcopy(r)
                                    for k, v in tdefault.__dict__.items():
                                        if not hasattr(tainted, k):
                                            setattr(tainted, k, v)
                                    taintedform[tainted_key] = tainted

                            for k, v in value.__dict__.items():
                                # loop through the attributes and value
                                # in the default dictionary
                                if not hasattr(r, k):
                                    # if the form dictionary doesn't have
                                    # the attribute, set it to the default
                                    setattr(r, k, v)
                            form[key] = r

                        elif isinstance(value, list):
                            # the default value is a list
                            val = form[key]
                            if not isinstance(val, list):
                                val = [val]

                            # First deal with tainted copies
                            if tainted_key in taintedform:
                                tainted = taintedform[tainted_key]
                                if not isinstance(tainted, list):
                                    tainted = [tainted]
                                for defitem in tdefault:
                                    if isinstance(defitem, record):
                                        for k, v in defitem.__dict__.items():
                                            for origitem in tainted:
                                                if not hasattr(origitem, k):
                                                    setattr(origitem, k, v)
                                    else:
                                        if defitem not in tainted:
                                            tainted.append(defitem)
                                taintedform[tainted_key] = tainted

                            elif tainted_key in tainteddefaults:
                                missesdefault = 0
                                for defitem in tdefault:
                                    if isinstance(defitem, record):
                                        try:
                                            for k, v in \
                                                    defitem.__dict__.items():
                                                for origitem in val:
                                                    if not hasattr(
                                                            origitem, k):
                                                        missesdefault = 1
                                                        raise NestedLoopExit
                                        except NestedLoopExit:
                                            break
                                    else:
                                        if defitem not in val:
                                            missesdefault = 1
                                            break
                                if missesdefault:
                                    tainted = deepcopy(val)
                                    for defitem in tdefault:
                                        if isinstance(defitem, record):
                                            for k, v in (
                                                    defitem.__dict__.items()):
                                                for origitem in tainted:
                                                    if not hasattr(
                                                            origitem, k):
                                                        setattr(origitem, k, v)
                                        else:
                                            if defitem not in tainted:
                                                tainted.append(defitem)
                                    taintedform[tainted_key] = tainted

                            for x in value:
                                # for each x in the list
                                if isinstance(x, record):
                                    # if the x is a record
                                    for k, v in x.__dict__.items():

                                        # loop through each
                                        # attribute and value in
                                        # the record

                                        for y in val:

                                            # loop through each
                                            # record in the form
                                            # list if it doesn't
                                            # have the attributes
                                            # in the default
                                            # dictionary, set them

                                            if not hasattr(y, k):
                                                setattr(y, k, v)
                                else:
                                    # x is not a record
                                    if x not in val:
                                        val.append(x)
                            form[key] = val
                        else:
                            # The form has the key, the key is not mapped
                            # to a record or sequence so do nothing
                            pass

            # Convert to tuples
            if tuple_items:
                for key in tuple_items.keys():
                    # Split the key and get the attr
                    k = key.split(".")
                    k, attr = '.'.join(k[:-1]), k[-1]
                    a = attr
                    new = ''
                    # remove any type_names in the attr
                    while not a == '':
                        a = a.split(":")
                        a, new = ':'.join(a[:-1]), a[-1]
                    attr = new
                    if k in form:
                        # If the form has the split key get its value
                        tainted_split_key = k
                        if should_be_tainted(k):
                            tainted_split_key = taint_string(k)
                        item = form[k]
                        if isinstance(item, record):
                            # if the value is mapped to a record, check if it
                            # has the attribute, if it has it, convert it to
                            # a tuple and set it
                            if hasattr(item, attr):
                                value = tuple(getattr(item, attr))
                                setattr(item, attr, value)
                        else:
                            # It is mapped to a list of  records
                            for x in item:
                                # loop through the records
                                if hasattr(x, attr):
                                    # If the record has the attribute
                                    # convert it to a tuple and set it
                                    value = tuple(getattr(x, attr))
                                    setattr(x, attr, value)

                        # Do the same for the tainted counterpart
                        if tainted_split_key in taintedform:
                            tainted = taintedform[tainted_split_key]
                            if isinstance(item, record):
                                seq = tuple(getattr(tainted, attr))
                                setattr(tainted, attr, seq)
                            else:
                                for trec in tainted:
                                    if hasattr(trec, attr):
                                        seq = getattr(trec, attr)
                                        seq = tuple(seq)
                                        setattr(trec, attr, seq)
                    else:
                        # the form does not have the split key
                        tainted_key = key
                        if should_be_tainted(key):
                            tainted_key = taint_string(key)
                        if key in form:
                            # if it has the original key, get the item
                            # convert it to a tuple
                            item = form[key]
                            item = tuple(form[key])
                            form[key] = item

                        if tainted_key in taintedform:
                            tainted = tuple(taintedform[tainted_key])
                            taintedform[tainted_key] = tainted

        if meth:
            if 'PATH_INFO' in environ:
                path = environ['PATH_INFO']
                while path[-1:] == '/':
                    path = path[:-1]
            else:
                path = ''
            other['PATH_INFO'] = f"{path}/{meth}"
            self._hacked_path = 1

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
            result = result + row % (
                html.escape(k, False), html.escape(repr(v), False))
        result = result + "</table><h3>cookies</h3><table>"
        for k, v in _filterPasswordFields(self.cookies.items()):
            result = result + row % (
                html.escape(k, False), html.escape(repr(v), False))
        result = result + "</table><h3>lazy items</h3><table>"
        for k, v in _filterPasswordFields(self._lazies.items()):
            result = result + row % (
                html.escape(k, False), html.escape(repr(v), False))
        result = result + "</table><h3>other</h3><table>"
        for k, v in _filterPasswordFields(self.other.items()):
            if k in ('PARENTS', 'RESPONSE'):
                continue
            result = result + row % (
                html.escape(k, False), html.escape(repr(v), False))

        for n in "0123456789":
            key = "URL%s" % n
            try:
                result = result + row % (key, html.escape(self[key], False))
            except KeyError:
                pass
        for n in "0123456789":
            key = "BASE%s" % n
            try:
                result = result + row % (key, html.escape(self[key], False))
            except KeyError:
                pass

        result = result + "</table><h3>environ</h3><table>"
        for k, v in self.environ.items():
            if k not in hide_key:
                result = result + row % (
                    html.escape(k, False), html.escape(repr(v), False))
        return result + "</table>"

    def __repr__(self):
        return f"<{self.__class__.__name__}, URL={self.get('URL')}>"

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


class WSGIRequest(HTTPRequest):
    # A request object for WSGI, no docstring to avoid being publishable.
    pass


class TaintRequestWrapper:

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


class TaintMethodWrapper:

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
class FileUpload:
    '''File upload objects

    File upload objects are used to represent file-uploaded data.

    File upload objects can be used just like files.

    In addition, they have a 'headers' attribute that is a dictionary
    containing the file-upload headers, and a 'filename' attribute
    containing the name of the uploaded file.
    '''

    # Allow access to attributes such as headers and filename so
    # that protected code can use DTML to work with FileUploads.
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, aFieldStorage):
        self.file = aFieldStorage.file
        self.headers = aFieldStorage.headers
        self.filename = aFieldStorage.filename
        self.name = aFieldStorage.name

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


class record:

    # Allow access to record methods and values from DTML
    __allow_access_to_unprotected_subobjects__ = 1
    _guarded_writes = 1

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
            f"'{key}': {value!r}"
            for key, value in sorted(self.__dict__.items()))

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


def use_builtin_xmlrpc(request):
    checker = queryUtility(IXmlrpcChecker)
    return checker is None or checker(request)
