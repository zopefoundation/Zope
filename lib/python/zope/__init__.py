# Knit any zope packages found on sys.path together
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)
