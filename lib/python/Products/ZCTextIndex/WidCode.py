# A byte-aligned encoding for lists of non-negative ints, using fewer bytes
# for smaller ints.  This is intended for lists of word ids (wids).  The
# ordinary string .find() method can be used to find the encoded form of a
# desired wid-string in an encoded wid-string.  As in UTF-8, the initial byte
# of an encoding can't appear in the interior of an encoding, so find() can't
# be fooled into starting a match "in the middle" of an encoding.

# Details:
#
# + Only the first byte of an encoding has the sign bit set.
#
# + The number of bytes in the encoding is encoded in unary at the start of
#   the first byte (i.e., an encoding with n bytes begins with n 1-bits
#   followed by a 0 bit).
#
# + Bytes beyond the first in an encoding have the sign bit clear, followed
#   by 7 bits of data.
#
# + The number of data bits in the first byte of an encoding varies.
#
# The int to be encoded can contain no more than 24 bits.
# XXX this could certainly be increased
#
# If it contains no more than 6 bits, 00abcdef, the encoding is
#     10abcdef
#
# If it contains 7 thru 12 bits,
#     0000abcd efghijkL
# the encoding is
#     110abcde 0fghijkL
#
# Static tables _encoding and _decoding capture all encodes and decodes for
# 12 or fewer bits.
#
# If it contains 13 thru 18 bits,
#    000000ab cdefghij kLmnopqr
# the encoding is
#    1110abcd 0efghijk 0Lmnopqr
#
# If it contains 19 thru 24 bits,
#    abcdefgh ijkLmnop qrstuvwx
# the encoding is
#    11110abc 0defghij 0kLmnopq 0rstuvwx


import re

def encode(wids):
    # Encode a list of wids as a string.
    wid2enc = _encoding
    n = len(wid2enc)
    return "".join([w < n and wid2enc[w] or _encode(w) for w in wids])

_encoding = [None] * 0x1000 # Filled later, and converted to a tuple

def _encode(w):
    assert 0x1000 <= w < 0x1000000
    b, c = divmod(w, 0x80)
    a, b = divmod(b, 0x80)
    s = chr(b) + chr(c)
    if a < 0x10:    # no more than 18 data bits
        return chr(a + 0xE0) + s
    a, b = divmod(a, 0x80)
    assert a < 0x4, (w, a, b, s)  # else more than 24 data bits
    return (chr(a + 0xF0) + chr(b)) + s

_prog = re.compile(r"[\x80-\xFF][\x00-\x7F]*")

def decode(code):
    # Decode a string into a list of wids.
    get = _decoding.get
    # Obscure:  while _decoding does have the key '\x80', its value is 0,
    # so the "or" here calls _decode('\x80') anyway.
    return [get(p) or _decode(p) for p in _prog.findall(code)]

_decoding = {} # Filled later

def _decode(s):
    if s == '\x80':
        # See comment in decode().  This is here to allow a trick to work.
        return 0
    if len(s) == 3:
        a, b, c = map(ord, s)
        assert a & 0xF0 == 0xE0 and not b & 0x80 and not c & 0x80
        return ((a & 0xF) << 14) | (b << 7) | c
    assert len(s) == 4, `s`
    a, b, c, d = map(ord, s)
    assert a & 0xF8 == 0xF0 and not b & 0x80 and not c & 0x80 and not d & 0x80
    return ((a & 0x7) << 21) | (b << 14) | (c << 7) | d

def _fill():
    global _encoding
    for i in range(0x40):
        s = chr(i + 0x80)
        _encoding[i] = s
        _decoding[s] = i
    for i in range(0x40, 0x1000):
        hi, lo = divmod(i, 0x80)
        s = chr(hi + 0xC0) + chr(lo)
        _encoding[i] = s
        _decoding[s] = i
    _encoding = tuple(_encoding)

_fill()

def test():
    for i in range(2**20):
        if i % 1000 == 0: print i
        wids = [i]
        code = encode(wids)
        assert decode(code) == wids, (wids, code, decode(code))

if __name__ == "__main__":
    test()
