from zExceptions import HTTPException


class HTTPExceptionHandler(object):

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        environ['Zope2.httpexceptions'] = self
        try:
            return self.application(environ, start_response)
        except HTTPException as exc:
            return exc(environ, start_response)


def main(app, global_conf=None):
    return HTTPExceptionHandler(app)
