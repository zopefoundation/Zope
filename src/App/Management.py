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
"""Standard management interface support
"""

from cgi import escape
import sys
import urllib

from zope.interface import implements
from AccessControl import getSecurityManager, Unauthorized
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import view_management_screens
from App.interfaces import INavigation
from App.special_dtml import HTMLFile
from App.special_dtml import DTMLFile
from ExtensionClass import Base
from zExceptions import Redirect


class Tabs(Base):
    """Mix-in provides management folder tab support."""

    security = ClassSecurityInfo()

    security.declarePublic('manage_tabs')
    manage_tabs=DTMLFile('dtml/manage_tabs', globals())


    manage_options  =()

    security.declarePublic('filtered_manage_options')
    def filtered_manage_options(self, REQUEST=None):

        validate=getSecurityManager().validate

        result=[]

        try:
            options=tuple(self.manage_options)
        except TypeError:
            options=tuple(self.manage_options())

        for d in options:

            filter=d.get('filter', None)
            if filter is not None and not filter(self):
                continue

            path=d.get('path', None)
            if path is None:
                    path=d['action']

            o=self.restrictedTraverse(path, None)
            if o is None:
                continue

            result.append(d)

        return result


    manage_workspace__roles__=('Authenticated',)
    def manage_workspace(self, REQUEST):
        """Dispatch to first interface in manage_options
        """
        options=self.filtered_manage_options(REQUEST)
        try:
            m=options[0]['action']
            if m=='manage_workspace':
                    raise TypeError
        except (IndexError, KeyError):
            raise Unauthorized, (
                'You are not authorized to view this object.')

        if m.find('/'):
            raise Redirect, (
                "%s/%s" % (REQUEST['URL1'], m))

        return getattr(self, m)(self, REQUEST)

    def tabs_path_default(self, REQUEST,
                          # Static var
                          unquote=urllib.unquote,
                          ):
        steps = REQUEST._steps[:-1]
        script = REQUEST['BASEPATH1']
        linkpat = '<a href="%s/manage_workspace">%s</a>'
        out = []
        url = linkpat % (escape(script, 1), '&nbsp;/')
        if not steps:
            return url
        last = steps.pop()
        for step in steps:
            script = '%s/%s' % (script, step)
            out.append(linkpat % (escape(script, 1), escape(unquote(step))))
        script = '%s/%s' % (script, last)
        out.append('<a class="strong-link" href="%s/manage_workspace">%s</a>'%
                   (escape(script, 1), escape(unquote(last))))
        return '%s%s' % (url, '/'.join(out))

    def tabs_path_info(self, script, path,
                       # Static vars
                       quote=urllib.quote,
                       ):
        out=[]
        while path[:1]=='/':
            path = path[1:]
        while path[-1:]=='/':
            path = path[:-1]
        while script[:1]=='/':
            script = script[1:]
        while script[-1:]=='/':
            script = script[:-1]
        path=path.split('/')[:-1]
        if script:
            path = [script] + path
        if not path:
            return ''
        script=''
        last=path[-1]
        del path[-1]
        for p in path:
            script="%s/%s" % (script, quote(p))
            out.append('<a href="%s/manage_workspace">%s</a>' % (script, p))
        out.append(last)
        return '/'.join(out)

InitializeClass(Tabs)


class Navigation(Base):
    """Basic navigation UI support"""

    implements(INavigation)

    security = ClassSecurityInfo()

    security.declareProtected(view_management_screens, 'manage')
    manage            =DTMLFile('dtml/manage', globals())

    security.declareProtected(view_management_screens, 'manage_menu')
    manage_menu       =DTMLFile('dtml/menu', globals())

    security.declareProtected(view_management_screens, 'manage_top_frame')
    manage_top_frame  =DTMLFile('dtml/manage_top_frame', globals())

    security.declareProtected(view_management_screens, 'manage_page_header')
    manage_page_header=DTMLFile('dtml/manage_page_header', globals())

    security.declareProtected(view_management_screens, 'manage_page_footer')
    manage_page_footer=DTMLFile('dtml/manage_page_footer', globals())

    security.declarePublic('manage_form_title')
    manage_form_title =DTMLFile('dtml/manage_form_title', globals(),
                                form_title='Add Form',
                                help_product=None,
                                help_topic=None)
    manage_form_title._setFuncSignature(
        varnames=('form_title', 'help_product', 'help_topic') )

    security.declarePublic('zope_quick_start')
    zope_quick_start=DTMLFile('dtml/zope_quick_start', globals())

    security.declarePublic('manage_copyright')
    manage_copyright=DTMLFile('dtml/copyright', globals())

    security.declarePublic('manage_zmi_logout')
    def manage_zmi_logout(self, REQUEST, RESPONSE):
        """Logout current user"""
        p = getattr(REQUEST, '_logout_path', None)
        if p is not None:
            return apply(self.restrictedTraverse(p))

        realm=RESPONSE.realm
        RESPONSE.setStatus(401)
        RESPONSE.setHeader('WWW-Authenticate', 'basic realm="%s"' % realm, 1)
        RESPONSE.setBody("""<html>
<head><title>Logout</title></head>
<body>
<p>
You have been logged out.
</p>
</body>
</html>""")
        return

    security.declarePublic('manage_zmi_prefs')
    manage_zmi_prefs=DTMLFile('dtml/manage_zmi_prefs', globals())

# Navigation doesn't have an inherited __class_init__ so doesn't get
# initialized automatically.

file = DTMLFile('dtml/manage_page_style.css', globals())
Navigation.security.declarePublic('manage_page_style.css')
setattr(Navigation, 'manage_page_style.css', file)

InitializeClass(Navigation)
