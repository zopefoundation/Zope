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

import sys
from Zope2.utilities.finder import ZopeFinder


def adduser(app, user, pwd):
    import transaction
    result = app.acl_users._doAddUser(user, pwd, ['Manager'], [])
    transaction.commit()
    return result


def main(argv=sys.argv):
    import sys
    try:
        user, pwd = argv[1], argv[2]
    except IndexError:
        print "%s <username> <password>" % argv[0]
        sys.exit(255)
    finder = ZopeFinder(argv)
    finder.filter_warnings()
    app = finder.get_app()
    result = adduser(app, user, pwd)
    if result:
        print "User %s created." % user
    else:
        print "Got no result back. User creation may have failed."
        print "Maybe the user already exists and nothing is done then."
        print "Or the implementation does not give info when it succeeds."

if __name__ == '__main__':
    main()
