"""XML-RPC support module

Written by Eric Kidd at UserLand software, with much help from Jim Fulton
at DC. This code hooks Zope up to Fredrik Lundh's Python XML-RPC library.

See http://www.xmlrpc.com/ and http://linux.userland.com/ for more
information about XML-RPC and Zope.
"""

import sys
from string import replace
from HTTPResponse import HTTPResponse
import xmlrpclib

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
    print '>>>>', data
    params, method = xmlrpclib.loads(data)
    # Translate '.' to '/' in meth to represent object traversal.
    method = replace(method, '.', '/')
    return method, params

def response(anHTTPResponse):
    """Return a valid ZPublisher response object

    Use data already gathered by the existing response.
    The new response will replace the existing response.
    """
    # As a first cut, lets just clone the response and
    # put all of the logic in our refined response class below.
    r=Response()
    r.__dict__.update(anHTTPResponse.__dict__)
    return r
    
    

########################################################################
# Possible implementation helpers:

class Response(HTTPResponse):
    """Customized HTTPResponse that handles XML-RPC-specific details.

    We override setBody to marhsall Python objects into XML-RPC. We
    also override exception to convert errors to XML-RPC faults.

    If these methods stop getting called, make sure that ZPublisher is
    using the xmlrpc.Response object created above and not the original
    HTTPResponse object from which it was cloned.

    It's probably possible to improve the 'exception' method quite a bit.
    The current implementation, however, should suffice for now.
    """
    
    def setBody(self, body, title='', is_error=0, bogus_str_search=None):
	if isinstance(body, xmlrpclib.Fault):
            # Convert Fault object to XML-RPC response.
            body=xmlrpclib.dumps(body, methodresponse=1)
        else:
            # Marshall our body as an XML-RPC response. Strings will be sent
            # strings, integers as integers, etc. We do *not* convert
            # everything to a string first.
            body = xmlrpclib.dumps((body,), methodresponse=1)
        # Set our body to the XML-RPC message, and fix our MIME type.
        HTTPResponse.setBody(self, body)
        self.setHeader('content-type', 'text/xml')
        print 'setBody', body
        return self

    def exception(self, fatal=0, info=None,
                  absuri_match=None, tag_search=None):
        # Fetch our exception info. t is type, v is value and tb is the
        # traceback object.
        if type(info) is type(()) and len(info)==3: t,v,tb = info
        else: t,v,tb = sys.exc_info()

        # Abort running transaction, if any:
        try: get_transaction().abort()
        except: pass

        # Create an appropriate Fault object. Unfortunately, we throw away
        # most of the debugging information. More useful error reporting is
        # left as an exercise for the reader.
        Fault=xmlrpclib.Fault
        f=None
        try:
            if isinstance(v, Fault):
                f=v
            elif isinstance(v, Exception):
                f=Fault(-1, "Unexpected Zope exception: " + str(v))
            else:
                f=Fault(-2, "Unexpected Zope error value: " + str(v))
        except:
            f=Fault(-3, "Unknown Zope fault type")

        # Do the damage.
        self.setBody(f)
        print 'Exception', f
        self.setStatus(200)

        return tb
