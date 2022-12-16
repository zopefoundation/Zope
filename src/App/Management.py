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

import html
import itertools
from urllib.parse import quote
from urllib.parse import unquote

import zope.event
from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import view_management_screens
from App.interfaces import ICSSPaths
from App.interfaces import IJSPaths
from App.interfaces import INavigation
from App.special_dtml import DTMLFile
from ExtensionClass import Base
from zope.interface import implementer


class Tabs(Base):
    """Mix-in provides management folder tab support."""

    security = ClassSecurityInfo()

    security.declarePublic('manage_tabs')  # NOQA: D001
    manage_tabs = DTMLFile('dtml/manage_tabs', globals())

    manage_options = ()

    @security.public
    def filtered_manage_options(self, REQUEST=None):
        result = []
        try:
            options = tuple(self.manage_options)
        except TypeError:
            options = tuple(self.manage_options())

        for d in options:
            filter_ = d.get('filter', None)
            if filter_ is not None and not filter_(self):
                continue

            path = d.get('path', None)
            if path is None:
                path = d['action']

            o = self.restrictedTraverse(path, None)
            if o is None:
                continue

            result.append(d)

        return result

    manage_workspace__roles__ = ('Authenticated',)

    def manage_workspace(self, REQUEST):
        """Dispatch to first interface in manage_options
        """
        options = self.filtered_manage_options(REQUEST)
        try:
            m = options[0]['action']
            if m == 'manage_workspace':
                raise TypeError
        except (IndexError, KeyError):
            raise Unauthorized(
                'You are not authorized to view this object.')

        if m.find('/'):
            return REQUEST.RESPONSE.redirect(f"{REQUEST['URL1']}/{m}")

        return getattr(self, m)(self, REQUEST)

    def tabs_path_length(self, REQUEST):
        return len(list(self.tabs_path_default(REQUEST)))

    def tabs_path_default(self, REQUEST):
        steps = REQUEST._steps[:-1]
        script = REQUEST['BASEPATH1']
        linkpat = '{0}/manage_workspace'
        yield {'url': linkpat.format(html.escape(script, True)),
               'title': 'Root',
               'last': not bool(steps)}
        if not steps:
            return
        last = steps.pop()
        for step in steps:
            script = f'{script}/{step}'
            yield {'url': linkpat.format(html.escape(script, True)),
                   'title': html.escape(unquote(step)),
                   'last': False}
        script = f'{script}/{last}'
        yield {'url': linkpat.format(html.escape(script, True)),
               'title': html.escape(unquote(last)),
               'last': True}

    def tabs_path_info(self, script, path):
        out = []
        while path[:1] == '/':
            path = path[1:]
        while path[-1:] == '/':
            path = path[:-1]
        while script[:1] == '/':
            script = script[1:]
        while script[-1:] == '/':
            script = script[:-1]
        path = path.split('/')[:-1]
        if script:
            path = [script] + path
        if not path:
            return ''
        script = ''
        last = path[-1]
        del path[-1]
        for p in path:
            script = f"{script}/{quote(p)}"
            out.append(f'<a href="{script}/manage_workspace">{p}</a>')
        out.append(last)
        return '/'.join(out)


InitializeClass(Tabs)


@implementer(INavigation)
class Navigation(Base):
    """Basic navigation UI support"""

    security = ClassSecurityInfo()

    security.declareProtected(view_management_screens, 'manage')  # NOQA: D001
    manage = DTMLFile('dtml/manage', globals())

    security.declareProtected(view_management_screens,  # NOQA: D001
                              'manage_menu')
    manage_menu = DTMLFile('dtml/menu', globals())

    security.declareProtected(view_management_screens,  # NOQA: D001
                              'manage_page_footer')
    manage_page_footer = DTMLFile('dtml/manage_page_footer', globals())

    security.declarePublic('manage_form_title')  # NOQA: D001
    manage_form_title = DTMLFile('dtml/manage_form_title', globals(),
                                 form_title='Add Form',
                                 help_product=None,
                                 help_topic=None)
    manage_form_title._setFuncSignature(
        varnames=('form_title', 'help_product', 'help_topic'))

    _manage_page_header = DTMLFile('dtml/manage_page_header', globals())

    @security.protected(view_management_screens)
    def manage_page_header(self, *args, **kw):
        """manage_page_header."""
        kw['css_urls'] = itertools.chain(
            itertools.chain(*zope.component.subscribers((self,), ICSSPaths)),
            self._get_zmi_additionals('zmi_additional_css_paths'))
        kw['js_urls'] = itertools.chain(
            itertools.chain(*zope.component.subscribers((self,), IJSPaths)),
            self._get_zmi_additionals('zmi_additional_js_paths'))
        return self._manage_page_header(*args, **kw)

    security.declareProtected(view_management_screens,  # NOQA: D001
                              'manage_navbar')
    manage_navbar = DTMLFile('dtml/manage_navbar', globals())

    security.declarePublic('zope_copyright')  # NOQA: D001
    zope_copyright = DTMLFile('dtml/copyright', globals())

    @security.public
    def manage_zmi_logout(self, REQUEST, RESPONSE):
        """Logout current user"""
        p = getattr(REQUEST, '_logout_path', None)
        if p is not None:
            return self.restrictedTraverse(*p)

        realm = RESPONSE.realm
        RESPONSE.setStatus(401)
        RESPONSE.setHeader('WWW-Authenticate', 'basic realm="%s"' % realm, 1)
        RESPONSE.setHeader('Content-Type', 'text/html')
        RESPONSE.setBody("""<html>
<head><title>Logout</title></head>
<body>
<p>
You have been logged out.
</p>
</body>
</html>""")
        return

    def _get_zmi_additionals(self, attrib):
        # Get additional assets for styling ZMI defined on properties in ZMI.
        additionals = getattr(self, attrib, ()) or ()
        if isinstance(additionals, str):
            additionals = (additionals, )
        return additionals


# Navigation doesn't have an inherited __class_init__ so doesn't get
# initialized automatically.
InitializeClass(Navigation)
