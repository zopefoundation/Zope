from zope.interface import implements
from interfaces import IAdaptable, IAdapted, IOrigin, IDestination

class Adaptable:
    implements(IAdaptable)

    def method(self):
        return "The method"

class Adapter:
    implements(IAdapted)

    def __init__(self, context):
        self.context = context

    def adaptedMethod(self):
        return "Adapted: %s" % self.context.method()

class Origin:
    implements(IOrigin)

class OriginalAdapter:
    implements(IDestination)

    def __init__(self, context):
        self.context = context

    def method(self):
        return "Original"

class OverrideAdapter:
    implements(IDestination)

    def __init__(self, context):
        self.context = context

    def method(self):
        return "Overridden"
