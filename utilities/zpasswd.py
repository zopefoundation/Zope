#!/usr/bin/env python
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
"""Zope password change system"""

__version__='$Revision: 1.2 $ '[11:-2]

import sys, string, sha, binascii, whrandom, getopt, getpass

try:
    from crypt import crypt
except ImportError:
    crypt = None

def generate_salt():
    """Generate a salt value for the crypt function."""
    salt_choices = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" \
                   "abcdefghijklmnopqrstuvwxyz" \
                   "0123456789./"
    return whrandom.choice(salt_choices)

def generate_passwd(password, encoding):
    if encoding == 'SHA':
        pw = '{SHA}' + binascii.b2a_base64(sha.new(password).digest())[:-1]
    elif encoding == 'CRYPT':
        pw = '{CRYPT}' + crypt(password, generate_salt())
    elif encoding == 'CLEARTEXT':
        pw = password

    return pw

def main(argv):
    short_options = ':u:p:e:d:'
    long_options = ['username=',
                    'password=',
                    'encoding=',
                    'domains=']

    usage = """%s [options] filename

If this program is called without command-line options, it will prompt
for all necessary information.  The available options are:

    -u / --username=
    Set the username to be used for the superuser

    -p / --password=
    Set the password

    -e / --encoding=
    Set the encryption/encoding rules.  Defaults to SHA-1. OPTIONAL

    -d / --domains=
    Set the domain names that the user user can log in from.  Defaults to
    any. OPTIONAL.

    Filename is not option, and should be the name of the file to store the
    information in.

Copyright (C) 1999 Digital Creations, Inc.
""" % argv[0]

    try:
        if len(argv) < 2:
            raise "CommandLineError"
        
        optlist, args = getopt.getopt(sys.argv[1:], short_options, long_options)

        if len(args) != 1:
            raise "CommandLineError"

        access_file = open(args[0], 'w')

        if len(optlist) > 0:
            # Set the sane defaults
            username = 'superuser'
            encoding = 'SHA'
            domains = ''
        
            for opt in optlist:
                if (opt[0] == '-u') or (opt[0] == '--username'):
                    username = opt[1]
                elif (opt[0] == '-p') or (opt[0] == '--password'):
                    password = opt[1]
                elif (opt[0] == '-e') or (opt[0] == '--encoding'):
                    encoding = opt[1]
                elif (opt[0] == '-d') or (opt[0] == '--domains'):
                    domains = opt[1]

            # Verify that we got what we need
            if not username or not password:
                raise "CommandLineError"

            access_file.write(username + ':' +
                              generate_passwd(password, encoding) +
                              domains)

        else:
            # Run through the prompts
            while 1:
                username = raw_input("Username: ")
                if username != '':
                    break
               
            while 1:
                password = getpass.getpass("Password: ")
                verify = getpass.getpass("Vefify password: ")
                if verify == password:
                    break
                else:
                    password = verify = ''
                    print "Password mismatch, please try again..."

            while 1:
                print """
Please choose a format from:

SHA - SHA-1 hashed password
CRYPT - UNIX-style crypt password
CLEARTEXT - no protection.
"""
                encoding = raw_input("Encoding: ")
                if encoding != '':
                    break

            domains = raw_input("Domain restrictions: ")

            access_file.write(username + ":" +
                      generate_passwd(password, encoding) +
                      domains)
            
    except "CommandLineError":
        sys.stderr.write(usage)
        sys.exit(1)

    
# If called from the command line
if __name__=='__main__': main(sys.argv)

