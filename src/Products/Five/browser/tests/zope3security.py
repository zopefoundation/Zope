from zope.publisher.browser import BrowserView
from zope.security.management import checkPermission

class Zope3SecurityView(BrowserView):

    def __call__(self, permission):
        if checkPermission(permission, self.context):
            return "Yes, you have the %r permission." % permission
        else:
            return "No, you don't have the %r permission." % permission
