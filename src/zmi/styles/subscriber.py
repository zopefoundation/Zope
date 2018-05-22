import zope.component
import zope.interface


@zope.component.adapter(zope.interface.Interface)
def css_paths(context):
    """Return paths to CSS files needed for the Zope 4 ZMI."""
    return (
        '/++resource++zmi/bootstrap-4.1.1/bootstrap.min.css',
        '/++resource++zmi/zopetello/css/zopetello.css',
        '/++resource++zmi/fontawesome-5.0.13/css/fontawesome-all.min.css',
    )


@zope.component.adapter(zope.interface.Interface)
def js_paths(context):
    """Return paths to JS files needed for the Zope 4 ZMI."""
    return (
        '/++resource++zmi/jquery-3.2.1.min.js',
        '/++resource++zmi/bootstrap-4.1.1/bootstrap.bundle.min.js',
    )
