

# Implement the manage_addProduct method of object managers
import Acquisition
from string import rfind

class ProductDispatcher(Acquisition.Implicit):
    " "

    def __bobo_traverse__(self, REQUEST, name):
        product=self.aq_acquire('_getProducts')()._product(name)
        dispatcher=FactoryDispatcher(product, self.aq_parent, REQUEST)
        return dispatcher.__of__(self)

class FactoryDispatcher(Acquisition.Implicit):
    " "

    def __init__(self, product, dest, REQUEST):
        self._product=product.__dict__
        self._d=dest
        v=REQUEST['URL']
        v=v[:rfind(v,'/')]
        self._u=v[:rfind(v,'/')]

    def Destination(self):
        "Return the destination for factory output"
        return self._d
    Destination__roles__=None

    def DestinationURL(self):
        "Return the URL for the destination for factory output"
        return self._u
    DestinationURL__roles__=None

    def __getattr__(self, name):
        d=self._product
        if d.has_key(name):  return d[name].__of__(self)
        raise AttributeError, name

