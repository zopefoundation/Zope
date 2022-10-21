##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
""" Add a Zope management user to the root Zope user folder """

import argparse
import sys

from Zope2.utilities.finder import ZopeFinder


def adduser(app, user, pwd):
    import transaction
    result = app.acl_users._doAddUser(user, pwd, ['Manager'], [])
    transaction.commit()
    return result


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        description='Add a Zope management user to the root Zope user folder.'
    )
    parser.add_argument(
        "-c",
        "--configuration",
        help="Path to Zope configuration file",
        nargs="?",
        type=str,
        default=None,
    )
    parser.add_argument("user", help="name of user to be created")
    parser.add_argument("password", help="new password for the user")
    args = parser.parse_args(argv[1:])
    finder = ZopeFinder(argv)
    finder.filter_warnings()
    app = finder.get_app(config_file=args.configuration)
    result = adduser(app, args.user, args.password)
    if result:
        print(f"User {args.user} created.")
    else:
        print("Got no result back. User creation may have failed.")
        print("Maybe the user already exists and nothing is done then.")
        print("Or the implementation does not give info when it succeeds.")


if __name__ == '__main__':
    main()
