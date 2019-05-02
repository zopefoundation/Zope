import zope.component
import zope.interface


@zope.component.adapter(zope.interface.Interface)
def css_paths(context):
    """Return paths to CSS files needed for the Zope 4 ZMI."""
    return (
        '/++resource++zmi/bootstrap-4.1.1/bootstrap.min.css',
        '/++resource++zmi/fontawesome-free-5.8.1/css/all.css',
        '/++resource++zmi/zmi_base.css',
    )


@zope.component.adapter(zope.interface.Interface)
def js_paths(context):
    """Return paths to JS files needed for the Zope 4 ZMI."""
    return (
        '/++resource++zmi/jquery-3.2.1.min.js',
        '/++resource++zmi/bootstrap-4.1.1/bootstrap.bundle.min.js',
        '/++resource++zmi/ace.ajax.org/ace.js',
        '/++resource++zmi/zmi_base.js',
    )
