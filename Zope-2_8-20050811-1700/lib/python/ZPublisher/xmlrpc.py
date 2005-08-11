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
"""XML-RPC support module

Written by Eric Kidd at UserLand software, with much help from Jim Fulton
at DC. This code hooks Zope up to Fredrik Lundh's Python XML-RPC library.

See http://www.xmlrpc.com/ and http://linux.userland.com/ for more
information about XML-RPC and Zope.
"""

import re
import sys, types
from HTTPResponse import HTTPResponse
import xmlrpclib

from zExceptions import Unauthorized

def parse_input(data):
    """Parse input data and return a method path and argument tuple

    The data is a string.
    """
    #
    # For example, with the input:
    #
    #   <?xml version="1.0"?>
    #   <methodCall>
    #      <methodName>examples.getStateName</methodName>
    #      <params>
    #         <param>
    #            <value><i4>41</i4></value>
    #            </param>
    #         </params>
    #      </methodCall>
    #
    # the function should return:
    #
    #     ('examples.getStateName', (41,))
    params, method = xmlrpclib.loads(data)
    # Translate '.' to '/' in meth to represent object traversal.
    method = method.replace('.', '/')
    return method, params

# See below
#
# def response(anHTTPResponse):
#     """Return a valid ZPublisher response object
#
#     Use data already gathered by the existing response.
#     The new response will replace the existing response.
#     """
#     # As a first cut, lets just clone the response and
#     # put all of the logic in our refined response class below.
#     r=Response()
#     r.__dict__.update(anHTTPResponse.__dict__)
#     return r

########################################################################
# Possible implementation helpers:

class Response:
    """Customized Response that handles XML-RPC-specific details.

    We override setBody to marhsall Python objects into XML-RPC. We
    also override exception to convert errors to XML-RPC faults.

    If these methods stop getting called, make sure that ZPublisher is
    using the xmlrpc.Response object created above and not the original
    HTTPResponse object from which it was cloned.

    It's probably possible to improve the 'exception' method quite a bit.
    The current implementation, however, should suffice for now.
    """
    
    _error_format = 'text/plain' # No html in error values

    # Because we can't predict what kind of thing we're customizing,
    # we have to use delegation, rather than inheritance to do the
    # customization.

    def __init__(self, real): self.__dict__['_real']=real

    def __getattr__(self, name): return getattr(self._real, name)
    def __setattr__(self, name, v): return setattr(self._real, name, v)
    def __delattr__(self, name): return delattr(self._real, name)

    def setBody(self, body, title='', is_error=0, bogus_str_search=None):
        if isinstance(body, xmlrpclib.Fault):
            # Convert Fault object to XML-RPC response.
            body=xmlrpclib.dumps(body, methodresponse=1, allow_none=True)
        else:
            if type(body) == types.InstanceType:
                # Avoid disclosing private members. Private members are
                # by convention named with a leading underscore char.
                orig = body.__dict__
                dict = {}
                for key in orig.keys():
                    if key[:1] != '_':
                        dict[key] = orig[key]
                body = dict

            # Marshall our body as an XML-RPC response. Strings will be sent
            # strings, integers as integers, etc. We do *not* convert
            # everything to a string first.
            # Previously this had special handling if the response
            # was a Python None. This is now patched in xmlrpclib to
            # allow Nones nested inside data structures too.
            try:
                body = xmlrpclib.dumps(
                    (body,), methodresponse=1, allow_none=True)
            except:
                self.exception()
                return
        # Set our body to the XML-RPC message, and fix our MIME type.
        self._real.setBody(body)
        self._real.setHeader('content-type', 'text/xml')
        return self

    def exception(self, fatal=0, info=None,
                  absuri_match=None, tag_search=None):
        # Fetch our exception info. t is type, v is value and tb is the
        # traceback object.
        if type(info) is type(()) and len(info)==3: t,v,tb = info
        else: t,v,tb = sys.exc_info()

        # Don't mask 404 respnses, as some XML-RPC libraries rely on the HTTP
        # mechanisms for detecting when authentication is required. Fixes Zope
        # Collector issue 525.
        if t == 'Unauthorized' or (
            isinstance(t, types.ClassType) and issubclass(t, Unauthorized)
            ):

            return self._real.exception(fatal=fatal, info=info)

        # Create an appropriate Fault object. Containing error information
        Fault=xmlrpclib.Fault
        f=None
        try:
            # Strip HTML tags from the error value
            vstr = str(v)
            remove = [r"<[^<>]*>", r"&[A-Za-z]+;"]
            for pat in remove:
                vstr = re.sub(pat, " ", vstr)
            from Globals import DevelopmentMode
            if DevelopmentMode:
                from traceback import format_exception
                value = '\n' + ''.join(format_exception(t, vstr, tb))
            else:
                value = '%s - %s' % (t, vstr)
                
            if isinstance(v, Fault):
                f=v
            elif isinstance(v, Exception):
                f=Fault(-1, 'Unexpected Zope exception: %s' % value)
            else:
                f=Fault(-2, 'Unexpected Zope error value: %s' % value)
        except:
            f=Fault(-3, "Unknown Zope fault type")

        # Do the damage.
        self.setBody(f)
        self._real.setStatus(200)

        return tb

response=Response
