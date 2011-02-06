##############################################################################
#
# Copyright (c) 2001,2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Zope user bootstrap system

Usage: %(PROGRAM)s [options] filename

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

    -h / --help
    Print this help text and exit.

    Filename is required and should be the name of the file to store the
    information in (usually "inituser" or "access").
"""
import sys,  sha, binascii, random, getopt, getpass, os

try:
    from crypt import crypt
except ImportError:
    crypt = None

PROGRAM = sys.argv[0]
COMMASPACE = ', '


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
    else:
        raise ValueError('Unsupported encoding: %s' % encoding)

    return pw

def write_generated_password(home, ac_path, username):
    pw_choices = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                  "abcdefghijklmnopqrstuvwxyz"
                  "0123456789!")
    acfile=open(ac_path, 'w')
    pw = ''
    for i in range(8):
        pw = pw + random.choice(pw_choices)
    acfile.write('%s:%s\n' % (username, generate_passwd(pw, 'SHA')))
    acfile.close()
    os.chmod(ac_path, 0644)
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

def get_password():
    while 1:
        password = getpass.getpass("Password: ")
        verify = getpass.getpass("Verify password: ")
        if verify == password:
            return password
        else:
            password = verify = ''
            print "Password mismatch, please try again..."

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


def usage(code, msg=''):
    print >> sys.stderr, __doc__ % globals()
    if msg:
        print >> sys.stderr, msg
    sys.exit(code)


def main():
    shortopts = 'u:p:e:d:h'
    longopts = ['username=',
                'password=',
                'encoding=',
                'domains=',
                'help']

    try:
        opts, args = getopt.getopt(sys.argv[1:], shortopts, longopts)
    except getopt.error, msg:
        usage(1, msg)

    # Defaults
    username = password = None
    domains = ''
    encoding = 'SHA'

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-u', '--username'):
            username = arg
        elif opt in ('-p', '--password'):
            password = arg
        elif opt in ('-e', '--encoding'):
            encoding = arg
        elif opt in ('-d', '--domains'):
            domains = ':' + arg

    # Extra command line arguments?
    if len(args) == 0:
        usage(1, 'filename is required')
    elif len(args) == 1:
        access_file = open(args[0], 'w')
    else:
        usage(1, 'Extra command line arguments: ' + COMMASPACE.join(args))

    if opts:
        # There were some command line args, so verify
        if username is not None and password is None:
            password = get_password()
    else:
        # No command line args, so prompt
        while 1:
            username = raw_input("Username: ")
            if username != '':
                break

        password = get_password()
        
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
        if domains:
            domains = ":" + domains

    # Done with prompts and args
    access_file.write(username + ":" +
                      generate_passwd(password, encoding) +
                      domains)


# If called from the command line
if __name__=='__main__':
    main()
