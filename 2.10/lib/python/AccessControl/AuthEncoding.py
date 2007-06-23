##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

__version__='$Revision: 1.9 $'[11:-2]

import sha, binascii
from binascii import b2a_base64, a2b_base64
from random import choice, randrange


class PasswordEncryptionScheme:  # An Interface

    def encrypt(pw):
        """
        Encrypt the provided plain text password.
        """

    def validate(reference, attempt):
        """
        Validate the provided password string.  Reference is the
        correct password, which may be encrypted; attempt is clear text
        password attempt.
        """


_schemes = []

def registerScheme(id, s):
    '''
    Registers an LDAP password encoding scheme.
    '''
    _schemes.append((id, '{%s}' % id, s))

def listSchemes():
    r = []
    for id, prefix, scheme in _schemes:
        r.append(id)
    return r


class SSHADigestScheme:
    '''
    SSHA is a modification of the SHA digest scheme with a salt
    starting at byte 20 of the base64-encoded string.
    '''
    # Source: http://developer.netscape.com/docs/technote/ldap/pass_sha.html

    def generate_salt(self):
        # Salt can be any length, but not more than about 37 characters
        # because of limitations of the binascii module.
        # 7 is what Netscape's example used and should be enough.
        # All 256 characters are available.
        salt = ''
        for n in range(7):
            salt += chr(randrange(256))
        return salt

    def encrypt(self, pw):
        pw = str(pw)
        salt = self.generate_salt()
        return b2a_base64(sha.new(pw + salt).digest() + salt)[:-1]

    def validate(self, reference, attempt):
        try:
            ref = a2b_base64(reference)
        except binascii.Error:
            # Not valid base64.
            return 0
        salt = ref[20:]
        compare = b2a_base64(sha.new(attempt + salt).digest() + salt)[:-1]
        return (compare == reference)

registerScheme('SSHA', SSHADigestScheme())


class SHADigestScheme:

    def encrypt(self, pw):
        return b2a_base64(sha.new(pw).digest())[:-1]

    def validate(self, reference, attempt):
        compare = b2a_base64(sha.new(attempt).digest())[:-1]
        return (compare == reference)

registerScheme('SHA', SHADigestScheme())


# Bogosity on various platforms due to ITAR restrictions
try:
    from crypt import crypt
except ImportError:
    crypt = None

if crypt is not None:

    class CryptDigestScheme:

        def generate_salt(self):
            choices = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                       "abcdefghijklmnopqrstuvwxyz"
                       "0123456789./")
            return choice(choices) + choice(choices)

        def encrypt(self, pw):
            return crypt(pw, self.generate_salt())

        def validate(self, reference, attempt):
            a = crypt(attempt, reference[:2])
            return (a == reference)

    registerScheme('CRYPT', CryptDigestScheme())


class MySQLDigestScheme:

    def encrypt(self, pw):
        nr = 1345345333L
        add = 7
        nr2 = 0x12345671L
        for i in pw:
            if i == ' ' or i == '\t':
                continue
            nr ^= (((nr & 63) + add) * ord(i)) + (nr << 8)
            nr2 += (nr2 << 8) ^ nr
            add += ord(i)
        r0 = nr & ((1L << 31) - 1L)
        r1 = nr2 & ((1L << 31) - 1L)
        return "%08lx%08lx" % (r0, r1)

    def validate(self, reference, attempt):
        a = self.encrypt(attempt)
        return (a == reference)

registerScheme('MYSQL', MySQLDigestScheme())


def pw_validate(reference, attempt):
    """Validate the provided password string, which uses LDAP-style encoding
    notation.  Reference is the correct password, attempt is clear text
    password attempt."""
    for id, prefix, scheme in _schemes:
        lp = len(prefix)
        if reference[:lp] == prefix:
            return scheme.validate(reference[lp:], attempt)
    # Assume cleartext.
    return (reference == attempt)

def is_encrypted(pw):
    for id, prefix, scheme in _schemes:
        lp = len(prefix)
        if pw[:lp] == prefix:
            return 1
    return 0

def pw_encrypt(pw, encoding='SSHA'):
    """Encrypt the provided plain text password using the encoding if provided
    and return it in an LDAP-style representation."""
    for id, prefix, scheme in _schemes:
        if encoding == id:
            return prefix + scheme.encrypt(pw)
    raise ValueError, 'Not supported: %s' % encoding

pw_encode = pw_encrypt  # backward compatibility
