##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

__version__='$Revision: 1.4 $'[11:-2]

import sha, binascii
from binascii import b2a_base64, a2b_base64
from string import upper
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
