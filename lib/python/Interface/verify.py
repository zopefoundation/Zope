from Exceptions import BrokenImplementation, DoesNotImplement, BrokenMethodImplementation
from Method import Method
from types import FunctionType
from _object import MethodTypes

def verify_class_implementation(iface, klass):
    """

    Verify that 'klass' correctly implements 'iface'.  This involves:

      o Making sure the klass defines all the necessary methods

      o Making sure the methods have the correct signature

      o Making sure the klass asserts that it implements the interface

    """

    if not iface.isImplementedByInstancesOf(klass):
        raise DoesNotImplement(iface)

    for n, d in iface.namesAndDescriptions():
        if not hasattr(klass, n):
            raise BrokenImplementation(iface, n)

        attr = getattr(klass, n)
        if type(attr) is FunctionType:
            meth = Method().fromFunction(attr, n)
        elif type(attr) in MethodTypes:
            meth = Method().fromMethod(attr, n)
        else:
            continue # must be an attribute...

        if d.getSignatureInfo() != meth.getSignatureInfo():
                raise BrokenMethodImplementation(n)

    return 1
