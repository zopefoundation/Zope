
import Basic, Util

class BitNumber(Basic.Base):
    """Numbers that can be interpreted as strings of bits

    they support & | ~ ^ << >>
    """

class Number(Basic.Base):
    """Numeric interface
    
    it is assumed that numeric types are embedded in each other in some 
    way (this is the Scheme numerical tower I think); they support
    operators + - *, usually / and %, perhaps **
    """

class Offsetable(Basic.Base):
    """Things that you can subtract and add numbers too

    e.g. Date-Time values.
    """

class Real(Number):
    """any subset of the real numbers (this includes ints and rationals)
    """

class Complex(Number):
    """has re and im fields (which are themselves real)
    """

class Exact(Number):
    """e.g. integers and rationals; also fixed point
    """

class AbritraryPrecision(Exact):
    """e.g. long, rationals
    """

class FixedPrecisionInt(Exact):
    """Fixed precision integers
    """

class FP64(FixedPrecisionInt):
    """int()  applied to these returns an integer that fits in 32 bits
    """

class FP32(FP64):
    """int()  applied to these returns an integer that fits in 32 bits
    """

class FP16(FP32):
    """int()  applied to these returns an integer that fits in 16 bits
    """

class FP8(FP16):
    """int()  applied to these returns an integer that fits in 16 bits
    """

class FP1(FP8):
    """int()  applied to these returns an integer that fits in 16 bits
    """

class Signed(FixedPrecisionInt):
    """These can be < 0
    """

class Unsigned(FixedPrecisionInt):
    """These can not be < 0
    """

class CheckedOverflow(FixedPrecisionInt):
    """raises OverflowError when results don't fit
    """

class UncheckedOverflow(FixedPrecisionInt):
    """take results module 2**N (for example)
    """

class FD(Exact):
    """fixed_decimal<n+m>

    a signed fixed decimal number with n digits
    before and m digits after the decimal point
    """

class Inexact(Number):
    """floating point arithmetic
    """

Util.assertTypeImplements(type(1), (FP32, BitNumber, Signed))
Util.assertTypeImplements(type(1L), (AbritraryPrecision, BitNumber, Signed))
Util.assertTypeImplements(type(1.0), (Inexact, BitNumber, Signed))


