

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
        if hasattr(product,'aq_base'): product=product.aq_base
        self._product=product
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
        p=self.__dict__['_product']
        d=p.__dict__
        if hasattr(p,name) and d.has_key(name):
            return d[name]
        raise AttributeError, name



