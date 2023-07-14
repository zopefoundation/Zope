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
from types import SimpleNamespace
from urllib.parse import parse_qsl
from urllib.parse import unquote
from urllib.parse import urlparse

from AccessControl.tainted import should_be_tainted as base_should_be_tainted
from AccessControl.tainted import taint_string
from multipart import Headers
from multipart import MultipartParser
from multipart import parse_options_header
from zExceptions import BadRequest
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

from .cookie import getCookieValuePolicy


# DOS attack protection -- limiting the amount of memory for forms
# probably should become configurable
FORM_MEMORY_LIMIT = 2 ** 20  # memory limit for forms
FORM_DISK_LIMIT = 2 ** 30    # disk limit for forms
FORM_MEMFILE_LIMIT = 4000    # limit for `BytesIO` -> temporary file switch


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
    _urls = ()
    _file = None

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
        self._fs = None
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
        k = get_env('HTTP_COOKIE', '')
        if k:
            parse_cookie(k, cookies)
        self.cookies = cookies
        self.taintedcookies = taint(cookies)

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

        # If 'QUERY_STRING' is not present in environ
        # FieldStorage will try to get it from sys.argv[1]
        # which is not what we need.
        if 'QUERY_STRING' not in environ:
            environ['QUERY_STRING'] = ''

        meth = None

        self._fs = fs = ZopeFieldStorage(fp, environ)
        self._file = fs.file

        if 'HTTP_SOAPACTION' in environ:
            # Stash XML request for interpretation by a SOAP-aware view
            other['SOAPXML'] = fs.value
            if 'CONTENT_TYPE' not in environ:
                environ['CONTENT_TYPE'] = 'application/soap+xml'

        if fs.list:
            fslist = fs.list
            tuple_items = {}
            defaults = {}
            converter = None

            for item in fslist:  # form data
                # Note:
                # we want to support 2 use cases
                # 1. the form data has been created by the browser
                # 2. the form data is free standing
                # A browser internally works with character data,
                # which it encodes for transmission to the server --
                # usually with `self.charset`. Therefore, we
                # usually expect the form data to represent data
                # in this charset.
                # We make this same assumption also for free standing
                # form data, i.e. we expect the form creator to know
                # the server's charset. However, sometimes data cannot
                # be represented in this charset (e.g. arbitrary binary
                # data). To cover this case, we decode data
                # with the `surrogateescape` error handler (see PEP 383).
                # It allows to retrieve the original byte sequence.
                # With an encoding modifier, the form creator
                # can specify the correct encoding used by a form field value.
                # Note: we always expect the form field name
                # to be representable with `self.charset`. As those
                # names are expected to be `ASCII`, this should be no
                # big restriction.
                # Note: the use of `surrogateescape` can lead to delayed
                # problems when surrogates reach the application because
                # they cannot be encoded with a standard error handler.
                # We might want to prevent this.
                key = item.name
                if key is None:
                    continue
                character_encoding = ""
                key = item.name.encode("latin-1").decode(
                    item.name_charset or self.charset)

                if hasattr(item, 'file') and \
                   hasattr(item, 'filename') and \
                   hasattr(item, 'headers'):
                    item = FileUpload(item, self.charset)
                else:
                    character_encoding = item.value_charset or self.charset
                    item = item.value.decode(
                        character_encoding, "surrogateescape")
                # from here on, `item` contains the field value
                # either as `FileUpload` or `str` with
                # `character_encoding` as encoding,
                # `key` the field name (`str`)

                flags = 0
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
                            # recode:
                            assert not isinstance(item, FileUpload), \
                                   "cannot recode files"
                            item = item.encode(
                                character_encoding, "surrogateescape")
                            character_encoding = type_name
                            # we do not use `surrogateescape` as
                            # we immediately want to determine
                            # an incompatible encoding modifier
                            item = item.decode(character_encoding)

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

                if flags:

                    # skip over empty fields
                    if flags & EMPTY:
                        continue

                    # Split the key and its attribute
                    if flags & REC:
                        key = key.split(".")
                        key, attr = ".".join(key[:-1]), key[-1]

                    # defer conversion
                    if flags & CONVERTED:
                        try:
                            if character_encoding and \
                               getattr(converter, "binary", False):
                                item = item.encode(character_encoding,
                                                   "surrogateescape")
                            item = converter(item)

                        except Exception:
                            if not item and \
                               not (flags & DEFAULT) and \
                               key in defaults:
                                item = defaults[key]
                                if flags & RECORD:
                                    item = getattr(item, attr)
                                if flags & RECORDS:
                                    item = getattr(item[-1], attr)
                            else:
                                raise

                    # Determine which dictionary to use
                    if flags & DEFAULT:
                        mapping_object = defaults
                    else:
                        mapping_object = form

                    # Insert in dictionary
                    if key in mapping_object:
                        if flags & RECORDS:
                            # Get the list and the last record
                            # in the list. reclist is mutable.
                            reclist = mapping_object[key]
                            x = reclist[-1]
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
                        else:
                            # it is not a record or list of records
                            found = mapping_object[key]
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
                        elif flags & RECORD:
                            # Create a new record, set its attribute
                            # and put it in the dictionary
                            if flags & SEQUENCE:
                                item = [item]
                            r = mapping_object[key] = record()
                            setattr(r, attr, item)
                        else:
                            # it is not a record or list of records
                            if flags & SEQUENCE:
                                item = [item]
                            mapping_object[key] = item

                else:
                    # This branch is for case when no type was specified.
                    mapping_object = form

                    # Insert in dictionary
                    if key in mapping_object:
                        # it is not a record or list of records
                        found = mapping_object[key]
                        if isinstance(found, list):
                            found.append(item)
                        else:
                            found = [found, item]
                            mapping_object[key] = found
                    else:
                        mapping_object[key] = item

            # insert defaults into form dictionary
            if defaults:
                for key, value in defaults.items():
                    if key not in form:
                        # if the form does not have the key,
                        # set the default
                        form[key] = value
                    else:
                        # The form has the key
                        if isinstance(value, record):
                            # if the key is mapped to a record, get the
                            # record
                            r = form[key]
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
                    else:
                        # the form does not have the split key
                        if key in form:
                            # if it has the original key, get the item
                            # convert it to a tuple
                            item = form[key]
                            item = tuple(form[key])
                            form[key] = item

            self.taintedform = taint(self.form)

        if method == 'POST' \
           and 'text/xml' in fs.headers.get('content-type', '') \
           and use_builtin_xmlrpc(self):
            # Ye haaa, XML-RPC!
            if meth is not None:
                raise BadRequest('method directive not supported for '
                                 'xmlrpc request')
            meth, self.args = xmlrpc.parse_input(fs.value)
            response = xmlrpc.response(response)
            other['RESPONSE'] = self.response = response
            self.maybe_webdav_client = 0

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
                v = self.other[key] = self._fs.value
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


class ValueDescriptor:
    """(non data) descriptor to compute `value` from `file`."""
    def __get__(self, inst, owner=None):
        if inst is None:
            return self
        file = inst.file
        try:
            fpos = file.tell()
        except Exception:
            fpos = None
        try:
            v = file.read()
            if fpos is None:
                # store the value as we cannot read it again
                inst.value = v
            return v
        finally:
            if fpos is not None:
                file.seek(fpos)


class ValueAccessor:
    value = ValueDescriptor()


class FormField(SimpleNamespace, ValueAccessor):
    """represent a single form field.

    Typical attributes:
    name
      the field name
    value
      the field value (`bytes`)
    name_charset, value_charset
      the charset for the name and value, respectively, or ``None``
      if no charset has been specified.

    File fields additionally have the attributes:
    file
      a binary file containing the file content
    filename
      the file's name as reported by the client
    headers
      a case insensitive dict with header information;
      usually `content-type` and `content-disposition`.

    Unless otherwise noted, `latin-1` decoded bytes
    are used to represent textual data.
    """

    name_charset = value_charset = None


class ZopeFieldStorage(ValueAccessor):
    def __init__(self, fp, environ):
        self.file = fp
        method = environ.get("REQUEST_METHOD", "GET").upper()
        url_qs = environ.get("QUERY_STRING", "")
        post_qs = ""
        hl = []
        content_type = environ.get("CONTENT_TYPE",
                                   "application/x-www-form-urlencoded")
        hl.append(("content-type", content_type))
        content_type, options = parse_options_header(content_type)
        content_type = content_type.lower()
        content_disposition = environ.get("CONTENT_DISPOSITION")
        if content_disposition is not None:
            hl.append(("content-disposition", content_disposition))
        self.headers = Headers(hl)
        parts = ()
        if method == "POST" \
           and content_type in \
           ("multipart/form-data", "application/x-www-form-urlencoded"):
            try:
                fpos = fp.tell()
            except Exception:
                fpos = None
            if content_type == "multipart/form-data":
                parts = MultipartParser(
                    fp, options["boundary"],
                    mem_limit=FORM_MEMORY_LIMIT,
                    disk_limit=FORM_DISK_LIMIT,
                    memfile_limit=FORM_MEMFILE_LIMIT,
                    charset="latin-1").parts()
            elif content_type == "application/x-www-form-urlencoded":
                post_qs = fp.read(FORM_MEMORY_LIMIT).decode("latin-1")
                if fp.read(1):
                    raise BadRequest("form data processing "
                                     "requires too much memory")
            if fpos is not None:
                fp.seek(fpos)
            else:
                # we cannot read the file again
                self.file = None
        self.list = fl = []
        add_field = fl.append
        post_opts = {}
        if options.get("charset"):
            post_opts["name_charset"] = post_opts["value_charset"] = \
                options["charset"]
        for qs, opts in ((url_qs, {}), (post_qs, post_opts)):
            for name, val in parse_qsl(
               qs,  # noqa: E121
               keep_blank_values=True, encoding="latin-1"):
                add_field(FormField(
                    name=name, value=val.encode("latin-1"), **opts))
        for part in parts:
            if part.filename is not None:
                # a file
                field = FormField(
                    name=part.name,
                    file=part.file,
                    filename=part.filename,
                    headers=part.headers)
            else:
                field = FormField(
                    name=part.name, value=part.raw,
                    value_charset=_mp_charset(part))
            add_field(field)


def _mp_charset(part):
    """the charset of *part*."""
    content_type = part.headers.get("Content-Type", "")
    _, options = parse_options_header(content_type)
    return options.get("charset")


# Original version: zope.publisher.browser.FileUpload
class FileUpload:
    '''File upload objects

    File upload objects are used to represent file-uploaded data.

    File upload objects can be used just like files.

    In addition, they have a 'headers' attribute that is a dictionary
    containing the file-upload headers, and a 'filename' attribute
    containing the name of the uploaded file.

    Note that file names in HTTP/1.1 use latin-1 as charset.  See
    https://github.com/zopefoundation/Zope/pull/1094#issuecomment-1459654636
    '''

    # Allow access to attributes such as headers and filename so
    # that protected code can use DTML to work with FileUploads.
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, aFieldStorage, charset=None):
        charset = charset or default_encoding
        self.file = aFieldStorage.file
        self.headers = aFieldStorage.headers
        # Prevent needless encode-decode when both charsets are the same.
        if charset != "latin-1":
            self.filename = aFieldStorage.filename\
                .encode("latin-1").decode(charset)
            self.name = aFieldStorage.name.encode("latin-1").decode(charset)
        else:
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
        result[name] = getCookieValuePolicy().load(name, value)

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


def taint(d):
    """return as ``dict`` the items from *d* which require tainting.

    *d* must be a ``dict`` with ``str`` keys and values recursively
    build from elementary values, ``list``, ``tuple``, ``record`` and
    ``dict``.
    """
    def should_taint(v):
        """check whether *v* needs tainting."""
        if isinstance(v, (list, tuple)):
            return any(should_taint(x) for x in v)
        if isinstance(v, (record, dict)):
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
        if isinstance(v, (bytes, str)) and should_be_tainted(v):
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
        if isinstance(v, dict):
            return v.__class__((_taint(k), _taint(v[k])) for k in v)
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
