import itertools

import zope.component
import zope.interface
from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import aq_parent


def prepend_authentication_path(context, path):
    """Prepend the path of the user folder.

    Because ++resource++zmi is protected, we generate URLs relative to the
    user folder of the logged-in user, so that the user can access the
    resources.
    """
    request = getattr(context, 'REQUEST', None)
    if request is None:
        return path
    user_folder = aq_parent(getSecurityManager().getUser())
    if user_folder is None:
        return path
    # prepend the authentication path, unless it is already part of the
    # virtual host root.
    authentication_path = []
    ufpp = aq_parent(user_folder).getPhysicalPath()
    vrpp = request.get("VirtualRootPhysicalPath") or ()
    for ufp, vrp in itertools.zip_longest(ufpp, vrpp):
        if ufp == vrp:
            continue
        authentication_path.append(ufp)

    parts = [
        p for p in itertools.chain(authentication_path, path.split("/")) if p]

    return request.physicalPathToURL(parts, relative=True)


@zope.component.adapter(zope.interface.Interface)
def css_paths(context):
    """Return paths to CSS files needed for the Zope 4 ZMI."""
    return (
        prepend_authentication_path(context, path)
        for path in (
            '/++resource++zmi/bootstrap-4.6.0/bootstrap.min.css',
            '/++resource++zmi/fontawesome-free-5.15.2/css/all.css',
            '/++resource++zmi/zmi_base.css',
        )
    )


@zope.component.adapter(zope.interface.Interface)
def js_paths(context):
    """Return paths to JS files needed for the Zope 4 ZMI."""
    return (
        prepend_authentication_path(context, path)
        for path in (
            '/++resource++zmi/jquery-3.5.1.min.js',
            '/++resource++zmi/bootstrap-4.6.0/bootstrap.bundle.min.js',
            '/++resource++zmi/ace.ajax.org/ace.js',
            '/++resource++zmi/zmi_base.js',
            '/++resource++zmi/zmi.localstorage.api.js',
        )
    )
