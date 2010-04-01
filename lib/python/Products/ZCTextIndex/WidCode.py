##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

# A byte-aligned encoding for lists of non-negative ints, using fewer bytes
# for smaller ints.  This is intended for lists of word ids (wids).  The
# ordinary string .find() method can be used to find the encoded form of a
# desired wid-string in an encoded wid-string.  As in UTF-8, the initial byte
# of an encoding can't appear in the interior of an encoding, so find() can't
# be fooled into starting a match "in the middle" of an encoding. Unlike
# UTF-8, the initial byte does not tell you how many continuation bytes
# follow; and there's no ASCII superset property.

# Details:
#
# + Only the first byte of an encoding has the sign bit set.
#
# + The first byte has 7 bits of data.
#
# + Bytes beyond the first in an encoding have the sign bit clear, followed
#   by 7 bits of data.
#
# + The first byte doesn't tell you how many continuation bytes are
#   following.  You can tell by searching for the next byte with the
#   high bit set (or the end of the string).
#
# The int to be encoded can contain no more than 28 bits.
#
# If it contains no more than 7 bits, 0abcdefg, the encoding is
#     1abcdefg
#
# If it contains 8 thru 14 bits,
#     00abcdef ghijkLmn
# the encoding is
#     1abcdefg 0hijkLmn
#
# Static tables _encoding and _decoding capture all encodes and decodes for
# 14 or fewer bits.
#
# If it contains 15 thru 21 bits,
#    000abcde fghijkLm nopqrstu
# the encoding is
#    1abcdefg 0hijkLmn 0opqrstu
#
# If it contains 22 thru 28 bits,
#    0000abcd efghijkL mnopqrst uvwxyzAB
# the encoding is
#    1abcdefg 0hijkLmn 0opqrstu 0vwxyzAB

assert 0x80**2 == 0x4000
assert 0x80**4 == 0x10000000

import re

def encode(wids):
    # Encode a list of wids as a string.
    wid2enc = _encoding
    n = len(wid2enc)
    return "".join([w < n and wid2enc[w] or _encode(w) for w in wids])

_encoding = [None] * 0x4000 # Filled later, and converted to a tuple

def _encode(w):
    assert 0x4000 <= w < 0x10000000
    b, c = divmod(w, 0x80)
    a, b = divmod(b, 0x80)
    s = chr(b) + chr(c)
    if a < 0x80:    # no more than 21 data bits
        return chr(a + 0x80) + s
    a, b = divmod(a, 0x80)
    assert a < 0x80, (w, a, b, s)  # else more than 28 data bits
    return (chr(a + 0x80) + chr(b)) + s

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
        assert a & 0x80 == 0x80 and not b & 0x80 and not c & 0x80
        return ((a & 0x7F) << 14) | (b << 7) | c
    assert len(s) == 4, `s`
    a, b, c, d = map(ord, s)
    assert a & 0x80 == 0x80 and not b & 0x80 and not c & 0x80 and not d & 0x80
    return ((a & 0x7F) << 21) | (b << 14) | (c << 7) | d

def _fill():
    global _encoding
    for i in range(0x80):
        s = chr(i + 0x80)
        _encoding[i] = s
        _decoding[s] = i
    for i in range(0x80, 0x4000):
        hi, lo = divmod(i, 0x80)
        s = chr(hi + 0x80) + chr(lo)
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
