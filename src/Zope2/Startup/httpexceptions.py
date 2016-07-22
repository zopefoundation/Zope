from zExceptions import (
    HTTPException,
    InternalError,
)

ERROR_HTML = """\
<html>
<head><title>Site Error</title></head>
<body bgcolor="#FFFFFF">
<h2>Site Error</h2>
<p>An error was encountered while publishing this resource.
</p>
<p><strong>Sorry, a site error occurred.</strong></p>

%s
<hr noshade="noshade"/>

<p>Troubleshooting Suggestions</p>

<ul>
<li>The URL may be incorrect.</li>
<li>The parameters passed to this resource may be incorrect.</li>
<li>A resource that this resource relies on may be
  encountering an error.</li>
</ul>

<p>If the error persists please contact the site maintainer.
Thank you for your patience.
</p></body></html>"""


class HTTPExceptionHandler(object):

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        environ['Zope2.httpexceptions'] = self
        try:
            return self.application(environ, start_response)
        except HTTPException as exc:
            return exc(environ, start_response)
        except Exception as exc:
            wrapper = InternalError()
            wrapper.setBody(ERROR_HTML % repr(exc))
            return wrapper(environ, start_response)


def main(app, global_conf=None):
    return HTTPExceptionHandler(app)
