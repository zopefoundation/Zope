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


import sys, re, unittest, cStringIO
import ZPublisher, ResultObject
import OFS.Application
import AccessControl.SecurityManagement


# Set up a publishable, non-ZODB Zope application.
app = OFS.Application.Application()
def index_html():
    " "
    return "This is index_html."
app.index_html = index_html  # Will index_html ever go away? ;-)
class BoboApplication:
    # OFS.Application has a __bobo_traverse__ that ZPublisher thinks
    # it should use to find the "real" root of the application.
    # This class gets around that.
    def __bobo_traverse__(self, request, name=None):
        return app

# ZPublisher will look for these vars.
bobo_application = BoboApplication()
zpublisher_validated_hook=AccessControl.SecurityManagement.newSecurityManager
__bobo_before__=AccessControl.SecurityManagement.noSecurityManager


class SecurityBase(unittest.TestCase) :
    """ Base class for all security tests
    $Id$
    """

    status_regex = re.compile("Status: ([0-9]{1,4}) (.*)",re.I)\


    ################################################################
    # print the object hierachy
    ################################################################

    def _testHierarchy(self):
        """ print all test objects, permissions and roles """
        self._PrintTestEnvironment(root=self.root.test)


    def _PrintTestEnvironment(self,root):
        """ print recursive all objects """

        print '....'*len(root.getPhysicalPath()),root.getId()

        folderObjs = []

        for id,obj in root.objectItems():

            if obj.meta_type in ['Folder','TestFolder']:
                folderObjs.append(obj)

            else:
                print '    '*(1+len(root.getPhysicalPath())),obj.getId(),
                print getattr(obj,"__roles__",(None,))

        for folder in folderObjs:
            self._PrintTestEnvironment(folder)


    ################################################################
    # Check functions for permissions, roles and friends
    ################################################################

    def _checkPermission(self, user, hier, perm, expected):
        """ permission check on an objects for a given user.

           -- 'user' is a user object as returned from a user folder

           -- 'hier' is the path to the object in the notation 'f1.f2.f3.obj'

           -- 'perm' is a permission name

           -- 'expected' is either 0 or 1
        """

        s = "self.root.%s" % hier
        obj = eval(s)

        res = user.has_permission(perm,obj)

        if res != expected:
            raise AssertionError, \
                self._perm_debug (s,perm,res,expected)


    def _checkRoles(self,hier,expected_roles=()):
        """ check roles for a given object.

           -- 'hier' is the path to the object in the notation 'f1.f2.f3.obj'

           -- 'expected_roles' is a sequence of expected roles

        """

        s = "self.root.%s.__roles__" % hier
        roles = eval(s)

        same = 0
        if roles is None or expected_roles is None:
            if (roles is None or tuple(roles) == ('Anonymous',)) and (
                expected_roles is None or
                tuple(expected_roles) == ('Anonymous',)):
                same = 1
        else:
            got = {}
            for r in roles: got[r] = 1
            expected = {}
            for r in expected_roles: expected[r] = 1
            if got == expected:  # Dict compare does the Right Thing.
                same = 1
        if not same:
            raise AssertionError, self._roles_debug(hier,roles,expected_roles)

    def _checkRequest(self,*args,**kw):
        """ perform a ZPublisher request """


        expected_code = kw.get('expected',200)
        del kw['expected']
        res = apply(self._request,args,kw)

        if expected_code != res.code:
            raise AssertionError, \
               self._request_debug(res,expected_code,args,kw)


    ################################################################
    # Debugging helpers when raising AssertionError
    ################################################################

    def _perm_debug(self, obj , perm, res, expected):
        s+= 'Object: %s' % obj
        s+= ', Permission: %s' % perm
        s+= ', has permission: %s' % res
        s+= ', expected: %s' % expected

        return s


    def _roles_debug(self,hier,got_roles,expected_roles):

        s = 'Object: %s' % hier
        s+= ', has roles: %s' % `got_roles`
        s+= ', expected roles: %s' % `expected_roles`

        return s


    def _request_debug(self,res,expected,args,kw):

        s = 'Args: %s' % str(args)
        s+= ', KW: %s' % str(kw)
        s+= '\n%s\n' % res.__str__(with_output=0,expected=expected)

        return s


    def _request(self,*args,**kw):
        """ perform a Zope request """

        io =cStringIO.StringIO()
        kw['fp']=io
        # Publish this module.
        testargs = (__name__,) + args
        real_stdout = sys.stdout
        garbage_out = cStringIO.StringIO()
        sys.stdout = garbage_out  # Silence, ZPublisher!
        try:
            ZPublisher.test(*testargs,**kw)
        finally:
            sys.stdout = real_stdout
        outp = io.getvalue()
        mo = self.status_regex.search(outp)

        code,txt = mo.groups()

        res = ResultObject.ResultObject()
        res.request     = args
        res.user        = kw.get('u','')
        res.code        = int(code)
        res.return_text = txt
        res.output      = outp

        return res
