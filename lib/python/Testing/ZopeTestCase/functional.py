#
# Support for functional unit testing in ZTC
# After Marius Gedminas' functional.py module for Zope3.
#

# $Id: functional.py,v 1.3 2004/09/12 16:49:59 shh42 Exp $

import sys, re, base64
import transaction
import sandbox


class Functional(sandbox.Sandboxed):
    '''Derive from this class and an xTestCase to get functional 
       testing support::
    
           class MyTest(Functional, ZopeTestCase):
               ...
    '''

    def publish(self, path, basic=None, env=None, extra=None, request_method='GET'):
        '''Publishes the object at 'path' returning an enhanced response object.'''

        from StringIO import StringIO
        from ZPublisher.Response import Response
        from ZPublisher.Test import publish_module

        # Commit the sandbox for good measure
        transaction.commit()

        if env is None: 
            env = {}
        if extra is None: 
            extra = {}

        request = self.app.REQUEST

        env['SERVER_NAME'] = request['SERVER_NAME']
        env['SERVER_PORT'] = request['SERVER_PORT']
        env['REQUEST_METHOD'] = request_method

        p = path.split('?')
        if len(p) == 1: 
            env['PATH_INFO'] = p[0]
        elif len(p) == 2: 
            [env['PATH_INFO'], env['QUERY_STRING']] = p
        else: 
            raise TypeError, ''

        if basic:
            env['HTTP_AUTHORIZATION'] = "Basic %s" % base64.encodestring(basic)

        outstream = StringIO()
        response = Response(stdout=outstream, stderr=sys.stderr) 

        publish_module('Zope2', response=response, environ=env, extra=extra)

        return ResponseWrapper(response, outstream, path)


class ResponseWrapper:
    '''Acts like a response object with some additional introspective methods.'''

    _bodyre = re.compile('^$^\n(.*)', re.MULTILINE | re.DOTALL)

    def __init__(self, response, outstream, path):
        self._response = response
        self._outstream = outstream
        self._path = path

    def getOutput(self):
        '''Returns the complete output, headers and all.'''
        return self._outstream.getvalue()

    def getBody(self):
        '''Returns the page body, i.e. the output par headers.'''
        body = self._bodyre.search(self.getOutput())
        if body is not None:
            body = body.group(1)
        return body

    def getPath(self):
        '''Returns the path used by the request.'''
        return self._path

    def __getattr__(self, name):
        return getattr(self._response, name)

