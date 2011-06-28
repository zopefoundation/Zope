from zExceptions import Forbidden
from zope.interface.interface import InterfaceClass
from zope.traversing import namespace


class resource(namespace.view):

    def traverse(self, name, ignored):
        # The context is important here, since it becomes the parent of the
        # resource, which is needed to generate the absolute URL.
        res = namespace.getResource(self.context, name, self.request)
        if isinstance(res, InterfaceClass):
            raise Forbidden('Access to traverser is forbidden.')
        return res
