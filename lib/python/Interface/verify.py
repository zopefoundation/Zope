
from Exceptions import BrokenImplementation, DoesNotImplement, BrokenMethodImplementation
from Method import Method
import types

def verify_class_implementation(iface, klass):
    """

    Verify that 'klass' correctly implements 'iface'.  This involves:

      o Making sure the klass defines all the necessary methods

      o Making sure the methods have the correct signature

      o Making sure the klass asserts that it implements the interface

    """

    if not iface.implementedByInstancesOf(klass):
        raise DoesNotImplement(iface)

    for n, d in iface.namesAndDescriptions():
        if not hasattr(klass, n):
            raise BrokenImplementation(iface, n)

        attr = getattr(klass, n)
        if type(attr) is types.FunctionType:
            meth = Method().fromFunction(attr, n)
        elif type(attr) is types.MethodType:
            meth = Method().fromMethod(attr, n)
        else:
            pass # must be an attribute...
        
        if d.getSignatureInfo() != meth.getSignatureInfo():
                raise BrokenMethodImplementation(n)
            
    return 1







