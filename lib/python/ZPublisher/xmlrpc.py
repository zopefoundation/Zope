"""Skeleton XML-RPC support module
"""

import HTTPResponse

def parse_input(data):
    """Parse input data and return a method path and argument tuple

    The data is a string (but maybe it should be a file, oh well,
    we'll come back to this if necessary.    
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

    return '', ()

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

class Response(HTTPResponse.HTTPResponse):
    """Customized HTTPResponse that handles XML-RPC-specific details

    I'm just guessing here.  XML-RPC wants all errors to be converted
    to XML and returned with an 200 OK status.

    You'll probably need to override a bunch of the error
    handling logic.
    """
    
