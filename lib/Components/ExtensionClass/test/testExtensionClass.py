"""ExtensionClass unit tests."""

from operator import truth
import unittest, string
import ExtensionClass


class MagicMethodTests(unittest.TestCase):
    """Test delegation to magic methods."""

    BaseClass = ExtensionClass.Base

    def fixup_inst(self, object):
        """A hook to allow acquisition tests based on this fixture."""
        return object

    #########################################################################
    # Test delegation of magic methods for attribute management.
    #########################################################################

    def test__getattr__(self):
        """Test __getattr__ delegation."""

        class PythonClass:
            def __getattr__(self, name):
                return 'bruce'

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert object.foo == 'bruce'

        object = self.fixup_inst(DerivedClass())
        assert object.foo == 'bruce'


    def test__setattr__(self):
        """Test __setattr__ delegation."""

        class PythonClass:
            def __setattr__(self, name, value):
                self.__dict__['bruce_%s' % name] = value

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        object.attr = 'value'
        assert object.bruce_attr == 'value'

        object = self.fixup_inst(DerivedClass())
        object.attr = 'value'
        assert object.bruce_attr == 'value'


    def test__delattr__(self):
        """Test __delattr__ delegation."""

        class PythonClass:
            def __delattr__(self, name):
                return

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        del object.foo

        object = self.fixup_inst(DerivedClass())
        del object.foo


    #########################################################################
    # Test delegation of magic methods for basic customization.
    #########################################################################

    def test__str__(self):
        """Test __str__ delegation."""

        class PythonClass:
            def __str__(self):
                return 'bruce'

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert str(object) == 'bruce'

        object = self.fixup_inst(DerivedClass())
        assert str(object) == 'bruce'


    def test__repr__(self):
        """Test __repr__ delegation."""

        class PythonClass:
            def __repr__(self):
                return 'bruce'

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert repr(object) == 'bruce'

        object = self.fixup_inst(DerivedClass())
        assert repr(object) == 'bruce'


    def test__cmp__(self):
        """Test __cmp__ delegation."""

        class PythonClass:
            def __cmp__(self, other):
                return 1

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert object > 1

        object = self.fixup_inst(DerivedClass())
        assert object > 1


    def test__hash__(self):
        """Test __hash__ delegation."""

        class PythonClass:
            def __hash__(self):
                return hash('bruce')

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert hash(object) == hash('bruce')

        object = self.fixup_inst(DerivedClass())
        assert hash(object) == hash('bruce')


    #########################################################################
    # Test delegation of rich comparison methods (new in Python 2.1).
    #########################################################################

    def test__lt__(self):
        """Test __lt__ delegation."""

        class PythonClass:
            def __lt__(self, other):
                return 1

            def __cmp__(self, other):
                raise AssertionError, 'Rich comparison not used!'

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert object < 1

        object = self.fixup_inst(DerivedClass())
        assert object < 1


    def test__le__(self):
        """Test __le__ delegation."""

        class PythonClass:
            def __le__(self, other):
                return 1

            def __cmp__(self, other):
                raise AssertionError, 'Rich comparison not used!'

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert object <= 1

        object = self.fixup_inst(DerivedClass())
        assert object <= 1


    def test__eq__(self):
        """Test __eq__ delegation."""

        class PythonClass:
            def __eq__(self, other):
                return 1

            def __cmp__(self, other):
                raise AssertionError, 'Rich comparison not used!'

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert object == 1

        object = self.fixup_inst(DerivedClass())
        assert object == 1


    def test__ne__(self):
        """Test __ne__ delegation."""

        class PythonClass:
            def __ne__(self, other):
                return 1

            def __cmp__(self, other):
                raise AssertionError, 'Rich comparison not used!'

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert object != 1

        object = self.fixup_inst(DerivedClass())
        assert object != 1


    def test__gt__(self):
        """Test __gt__ delegation."""

        class PythonClass:
            def __gt__(self, other):
                return 1

            def __cmp__(self, other):
                raise AssertionError, 'Rich comparison not used!'

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert object > 1

        object = self.fixup_inst(DerivedClass())
        assert object > 1


    def test__ge__(self):
        """Test __ge__ delegation."""

        class PythonClass:
            def __ge__(self, other):
                return 1

            def __cmp__(self, other):
                raise AssertionError, 'Rich comparison not used!'

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert object >= 1

        object = self.fixup_inst(DerivedClass())
        assert object >= 1


    #########################################################################
    # Test delegation of truth semantics, use of __nonzero__ and __len__.
    #########################################################################

    def testTruthSemanticsDefault(self):
        """Test truth semantics (default)."""

        class PythonClass:
            pass

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert truth(object) == 1

        object = self.fixup_inst(DerivedClass())
        assert truth(object) == 1


    def testTruthSemanticsWithNonZero(self):
        """Test truth semantics with __nonzero__."""

        class PythonClass:
            result = 0
            def __nonzero__(self):
                return self.result

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert truth(object) == 0

        object = self.fixup_inst(DerivedClass())
        assert truth(object) == 0

        PythonClass.result = 1

        object = PythonClass()
        assert truth(object) == 1

        object = self.fixup_inst(DerivedClass())
        assert truth(object) == 1


    def testTruthSemanticsWithLen(self):
        """Test truth semantics with __len__."""

        class PythonClass:
            result = 0
            def __len__(self):
                return self.result

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert truth(object) == 0

        object = self.fixup_inst(DerivedClass())
        assert truth(object) == 0

        PythonClass.result = 1

        object = PythonClass()
        assert truth(object) == 1

        object = self.fixup_inst(DerivedClass())
        assert truth(object) == 1


    def testTruthSemanticsWithNonZeroAndLen(self):
        """Test truth semantics with __nonzero__ and __len__."""

        class PythonClass:
            nn = 0
            ll = 1
            def __nonzero__(self):
                return self.nn

            def __len__(self):
                return self.ll

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert truth(object) == 0
        assert len(object) == 1

        object = self.fixup_inst(DerivedClass())
        assert truth(object) == 0
        assert len(object) == 1

        PythonClass.nn = 1
        PythonClass.ll = 0

        object = PythonClass()
        assert truth(object) == 1
        assert len(object) == 0

        object = self.fixup_inst(DerivedClass())
        assert truth(object) == 1
        assert len(object) == 0


    #########################################################################
    # Test delegation of overridable binary arithmetic operations.
    #########################################################################

    def test__add__(self):
        """Test __add__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __add__(self, other):
                return self.value + other

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        assert object + 1 == 2

        object = self.fixup_inst(DerivedClass(1))
        assert object + 1 == 2


    def test__sub__(self):
        """Test __sub__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __sub__(self, other):
                return self.value - other

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(2)
        assert object - 1 == 1

        object = self.fixup_inst(DerivedClass(2))
        assert object - 1 == 1


    def test__mul__(self):
        """Test __mul__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __mul__(self, other):
                return self.value * other

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(2)
        assert object * 2 == 4

        object = self.fixup_inst(DerivedClass(2))
        assert object * 2 == 4


    def test__div__(self):
        """Test __div__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __div__(self, other):
                return self.value / other

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(4)
        assert object / 2 == 2

        object = self.fixup_inst(DerivedClass(4))
        assert object / 2 == 2


    def test__mod__(self):
        """Test __mod__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __mod__(self, other):
                return self.value % other

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(101)
        assert object % 10 == 1

        object = self.fixup_inst(DerivedClass(101))
        assert object % 10 == 1


    def test__divmod__(self):
        """Test __divmod__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __divmod__(self, other):
                return divmod(self.value, other)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(101)
        assert divmod(object, 10) == (10, 1)

        object = self.fixup_inst(DerivedClass(101))
        assert divmod(object, 10) == (10, 1)


    def test__pow__(self):
        """Test __pow__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __pow__(self, other, modulo=None):
                return self.value ** other

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(10)
        assert object ** 2 == 100

        object = self.fixup_inst(DerivedClass(10))
        assert object ** 2 == 100


    def test__lshift__(self):
        """Test __lshift__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __lshift__(self, other):
                return self.value << other

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(100)
        assert object << 2 == 400

        object = self.fixup_inst(DerivedClass(100))
        assert object << 2 == 400


    def test__rshift__(self):
        """Test __rshift__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __rshift__(self, other):
                return self.value >> other

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(100)
        assert object >> 2  == 25

        object = self.fixup_inst(DerivedClass(100))
        assert object >> 2 == 25


    def test__and__(self):
        """Test __and__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __and__(self, other):
                return self.value & other

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        assert object & 1 == 1

        object = self.fixup_inst(DerivedClass(1))
        assert object & 1 == 1


    def test__xor__(self):
        """Test __xor__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __xor__(self, other):
                return self.value ^ other

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        assert object ^ 1 == 0

        object = self.fixup_inst(DerivedClass(1))
        assert object ^ 1 == 0


    def test__or__(self):
        """Test __or__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __or__(self, other):
                return self.value | other

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        assert object | 1 == 1

        object = self.fixup_inst(DerivedClass(1))
        assert object | 1 == 1


    #########################################################################
    # Test delegation of reflected binary arithmetic operations.
    #########################################################################

    def test__radd__(self):
        """Test __radd__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __radd__(self, other):
                return self.value + other

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        assert 1 + object == 2

        object = self.fixup_inst(DerivedClass(1))
        assert 1 + object == 2


    def test__rsub__(self):
        """Test __rsub__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __rsub__(self, other):
                return other - self.value

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(2)
        assert 2 - object == 0

        object = self.fixup_inst(DerivedClass(2))
        assert 2 - object == 0


    def test__rmul__(self):
        """Test __rmul__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __rmul__(self, other):
                return other * self.value

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(2)
        assert 2 * object == 4

        object = self.fixup_inst(DerivedClass(2))
        assert 2 * object == 4


    def test__rdiv__(self):
        """Test __rdiv__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __rdiv__(self, other):
                return other / self.value

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(4)
        assert 12 / object == 3

        object = self.fixup_inst(DerivedClass(4))
        assert 12 / object == 3


    def test__rmod__(self):
        """Test __rmod__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __rmod__(self, other):
                return other % self.value

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(10)
        assert 101 % object == 1

        object = self.fixup_inst(DerivedClass(10))
        assert 101 % object == 1


    def test__rdivmod__(self):
        """Test __rdivmod__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __rdivmod__(self, other):
                return divmod(other, self.value)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(10)
        assert divmod(101, object) == (10, 1)

        object = self.fixup_inst(DerivedClass(10))
        assert divmod(101, object) == (10, 1)


    def test__rpow__(self):
        """Test __rpow__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __rpow__(self, other):
                return other ** self.value

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(10)
        assert 2 ** object == 100

        object = self.fixup_inst(DerivedClass(10))
        assert 2 ** object == 100


    def test__rlshift__(self):
        """Test __rlshift__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __rlshift__(self, other):
                return other << self.value

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(2)
        assert 100 << object == 400

        object = self.fixup_inst(DerivedClass(2))
        assert 100 << object == 400


    def test__rrshift__(self):
        """Test __rrshift__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __rrshift__(self, other):
                return other >> self.value

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(2)
        assert 100 >> object  == 25

        object = self.fixup_inst(DerivedClass(2))
        assert 100 >> object  == 25


    def test__rand__(self):
        """Test __rand__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __rand__(self, other):
                return other & self.value

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        assert 1 & object == 1

        object = self.fixup_inst(DerivedClass(1))
        assert 1 & object == 1


    def test__rxor__(self):
        """Test __rxor__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __rxor__(self, other):
                return other ^ self.value

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        assert 1 ^ object == 0

        object = self.fixup_inst(DerivedClass(1))
        assert 1 ^ object == 0


    def test__ror__(self):
        """Test __ror__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __ror__(self, other):
                return other | self.value

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        assert 1 | object == 1

        object = self.fixup_inst(DerivedClass(1))
        assert 1 | object == 1


    #########################################################################
    # Test delegation of augmented assignment operations.
    #########################################################################

    def test__iadd__(self):
        """Test __iadd__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __iadd__(self, other):
                return self.__class__(self.value + other)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        object = object + 1
        assert object.value == 2

        object = self.fixup_inst(DerivedClass(1))
        object = object + 1
        assert object.value == 2


    def test__isub__(self):
        """Test __isub__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __isub__(self, other):
                return self.__class__(self.value - other)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(2)
        object -= 1
        assert object.value == 1

        object = self.fixup_inst(DerivedClass(2))
        object -= 1
        assert object.value == 1


    def test__imul__(self):
        """Test __imul__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __imul__(self, other):
                return self.__class__(self.value * other)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(2)
        object *= 2
        assert object.value == 4

        object = self.fixup_inst(DerivedClass(2))
        object *= 2
        assert object.value == 4


    def test__idiv__(self):
        """Test __idiv__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __idiv__(self, other):
                return self.__class__(self.value / other)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(4)
        object /= 2
        assert object.value == 2

        object = self.fixup_inst(DerivedClass(4))
        object /= 2
        assert object.value == 2


    def test__imod__(self):
        """Test __imod__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __imod__(self, other):
                return self.__class__(self.value % other)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(101)
        object %= 10
        assert object.value == 1

        object = self.fixup_inst(DerivedClass(101))
        object %= 10
        assert object.value == 1


    def test__ipow__(self):
        """Test __ipow__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __ipow__(self, other):
                return self.__class__(self.value ** other)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(10)
        object **= 2
        assert object.value == 100

        object = self.fixup_inst(DerivedClass(10))
        object **= 2
        assert object.value == 100


    def test__ilshift__(self):
        """Test __ilshift__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __ilshift__(self, other):
                return self.__class__(self.value << other)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(100)
        object <<= 2
        assert object.value == 400

        object = self.fixup_inst(DerivedClass(100))
        object <<= 2
        assert object.value == 400


    def test__irshift__(self):
        """Test __irshift__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __irshift__(self, other):
                return self.__class__(self.value >> other)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(100)
        object >>= 2
        assert object.value == 25

        object = self.fixup_inst(DerivedClass(100))
        object >>= 2
        assert object.value == 25


    def test__iand__(self):
        """Test __iand__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __iand__(self, other):
                return self.__class__(self.value & other)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        object &= 1
        assert object.value == 1

        object = self.fixup_inst(DerivedClass(1))
        object &= 1
        assert object.value == 1


    def test__ixor__(self):
        """Test __ixor__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __ixor__(self, other):
                return self.__class__(self.value ^ other)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        object ^= 1
        assert object.value == 0

        object = self.fixup_inst(DerivedClass(1))
        object ^= 1
        assert object.value == 0


    def test__ior__(self):
        """Test __ior__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __ior__(self, other):
                return self.__class__(self.value | other)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        object |= 1
        assert object.value == 1

        object = self.fixup_inst(DerivedClass(1))
        object |= 1
        assert object.value == 1


    #########################################################################
    # Test delegation of unary arithmetic operations.
    #########################################################################

    def test__pos__(self):
        """Test __pos__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __pos__(self):
                if self.value < 0:
                    return self.__class__(-(self.value))
                return self.__class__(self.value)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(-1)
        object = +(object)
        assert object.value == 1

        object = self.fixup_inst(DerivedClass(-1))
        object = +(object)
        assert object.value == 1


    def test__neg__(self):
        """Test __neg__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __neg__(self):
                return self.__class__(-(self.value))

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        object = -(object)
        assert object.value == -1

        object = self.fixup_inst(DerivedClass(1))
        object = -(object)
        assert object.value == -1


    def test__abs__(self):
        """Test __abs__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __abs__(self):
                return self.__class__(abs(self.value))

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(-1)
        object = abs(object)
        assert object.value == 1

        object = self.fixup_inst(DerivedClass(-1))
        object = abs(object)
        assert object.value == 1


    def test__invert__(self):
        """Test __invert__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __invert__(self):
                return self.__class__(~(self.value))

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(9)
        object = ~(object)
        assert object.value == -10

        object = self.fixup_inst(DerivedClass(9))
        object = ~(object)
        assert object.value == -10


    #########################################################################
    # Test delegation of numeric type coercion.
    #########################################################################

    def test__int__(self):
        """Test __int__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __int__(self):
                return int(self.value)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        assert int(object) == 1

        object = self.fixup_inst(DerivedClass(1))
        assert int(object) == 1


    def test__long__(self):
        """Test __long__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __long__(self):
                return long(self.value)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        assert long(object) == long(1)

        object = self.fixup_inst(DerivedClass(1))
        assert long(object) == long(1)


    def test__float__(self):
        """Test __float__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __float__(self):
                return float(self.value)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        assert float(object) == float(1)

        object = self.fixup_inst(DerivedClass(1))
        assert float(object) == float(1)


    def test__complex__(self):
        """Test __complex__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __complex__(self):
                return complex(self.value)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(1)
        assert complex(object) == complex(1)

        object = self.fixup_inst(DerivedClass(1))
        assert complex(object) == complex(1)


    #########################################################################
    # Test delegation of overridable __oct__ and __hex__
    #########################################################################

    def test__oct__(self):
        """Test __oct__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __oct__(self):
                return oct(self.value)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(10)
        assert oct(object) == '012'

        object = self.fixup_inst(DerivedClass(10))
        assert oct(object) == '012'


    def test__hex__(self):
        """Test __hex__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __hex__(self):
                return hex(self.value)

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(10)
        assert hex(object) == '0xa'

        object = self.fixup_inst(DerivedClass(10))
        assert hex(object) == '0xa'


    #########################################################################
    # Test delegation of mixed-mode coercion
    #########################################################################

    def test__coerce__(self):
        """Test __coerce__ delegation."""

        class PythonClass:
            def __init__(self, value):
                self.value = value
                
            def __coerce__(self, other):
                return (self.value, int(other))

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass(10)
        assert coerce(object, 10.0) == (10, 10)

        object = self.fixup_inst(DerivedClass(10))
        assert coerce(object, 10.0) == (10, 10)



    #########################################################################
    # Test delegation of overridable sequence protocol methods.
    #########################################################################

    def test__contains__(self):
        """Test __contains__ delegation."""

        class PythonClass:
            def __contains__(self, item):
                return 1

        class DerivedClass(self.BaseClass, PythonClass):
            pass

        object = PythonClass()
        assert 's' in object

        object = self.fixup_inst(DerivedClass())
        assert 's' in object





class ExtensionClassTests(MagicMethodTests):
    """Test ExtensionClass"""
    pass







def test_suite():
    suite_01 = unittest.makeSuite(ExtensionClassTests)
    return unittest.TestSuite((suite_01,))

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
