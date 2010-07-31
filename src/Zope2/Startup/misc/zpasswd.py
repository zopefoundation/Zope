#!/usr/bin/env python
##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Zope user bootstrap system"""

import sys,  sha, binascii, random, getopt, getpass, os

try:
    from crypt import crypt
except ImportError:
    crypt = None

def generate_salt():
    """Generate a salt value for the crypt function."""
    salt_choices = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    "abcdefghijklmnopqrstuvwxyz"
                    "0123456789./")
    return random.choice(salt_choices)+random.choice(salt_choices)

def generate_passwd(password, encoding):
    encoding=encoding.upper()
    if encoding == 'SHA':
        pw = '{SHA}' + binascii.b2a_base64(sha.new(password).digest())[:-1]
    elif encoding == 'CRYPT':
        pw = '{CRYPT}' + crypt(password, generate_salt())
    elif encoding == 'CLEARTEXT':
        pw = password

    return pw

def write_generated_password(home, ac_path, username):
    pw_choices = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                  "abcdefghijklmnopqrstuvwxyz"
                  "0123456789!")
    acfile=open(ac_path, 'w')
    pw = ''
    for i in range(8):
        pw = pw + random.choice(pw_choices)
    acfile.write('%s:%s' % (username, generate_passwd(pw, 'SHA')))
    acfile.close()
    os.system('chmod 644 %s' % ac_path)
    return pw

def write_access(home, user='', group=''):
    ac_path=os.path.join(home, 'access')
    if not os.path.exists(ac_path):
        print '-'*78
        print 'creating default access file'
        pw = write_generated_password(home, ac_path, 'emergency')
        print """Note:
        The emergency user name and password are 'emergency'
        and '%s'.

        You can change the emergency name and password with the
        zpasswd script.  To find out more, type:

        %s zpasswd.py
        """ % (pw, sys.executable)

        import do; do.ch(ac_path, user, group)

def write_inituser(home, user='', group=''):
    ac_path=os.path.join(home, 'inituser')
    if not os.path.exists(ac_path):
        print '-'*78
        print 'creating default inituser file'
        pw = write_generated_password(home, ac_path, 'admin')
        print """Note:
        The initial user name and password are 'admin'
        and '%s'.

        You can change the name and password through the web
        interface or using the 'zpasswd.py' script.
        """ % pw

        import do; do.ch(ac_path, user, group)


class CommandLineError(Exception):
    pass

def main(argv):
    short_options = ':u:p:e:d:'
    long_options = ['username=',
                    'password=',
                    'encoding=',
                    'domains=']

    usage = """Usage: %s [options] filename
If this program is called without command-line options, it will prompt
for all necessary information.  The available options are:

    -u / --username=
    Set the username to be used for the initial user or the emergency user

    -p / --password=
    Set the password

    -e / --encoding=
    Set the encryption/encoding rules.  Defaults to SHA-1. OPTIONAL

    -d / --domains=
    Set the domain names that the user user can log in from.  Defaults to
    any. OPTIONAL.

    Filename is required and should be the name of the file to store the
    information in (usually "inituser" or "access").

Copyright (C) 1999, 2000 Digital Creations, Inc.
""" % argv[0]

    try:
        if len(argv) < 2:
            raise CommandLineError, "Not enough arguments!"

        optlist, args = getopt.getopt(sys.argv[1:], short_options, long_options)

        if len(args) != 1:
            raise CommandLineError, "Only one filename allowed!"

        access_file = open(args[0], 'w')

        if len(optlist) > 0:
            # Set the sane defaults
            username = ''
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
                    domains = ":" + opt[1]

            # Verify that we got what we need
            if not username or not password:
                raise CommandLineError, "Must specify username and password."

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
                verify = getpass.getpass("Verify password: ")
                if verify == password:
                    break
                else:
                    password = verify = ''
                    print "Password mismatch, please try again..."

            while 1:
                print """
Please choose a format from:

SHA - SHA-1 hashed password (default)
CRYPT - UNIX-style crypt password
CLEARTEXT - no protection
"""
                encoding = raw_input("Encoding: ")
                if encoding == '':
                    encoding = 'SHA'
                    break
                if encoding.upper() in ['SHA', 'CRYPT', 'CLEARTEXT']:
                    break

            domains = raw_input("Domain restrictions: ")
            if domains: domains = ":" + domains

            access_file.write(username + ":" +
                              generate_passwd(password, encoding) +
                              domains)

    except CommandLineError, v:
        sys.stderr.write(usage)
        sys.stderr.write("\n\n%s" % v)
        sys.exit(1)


# If called from the command line
if __name__=='__main__':
    main(sys.argv)
