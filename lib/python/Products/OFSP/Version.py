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
"""Version object"""

__version__='$Revision: 1.55 $'[11:-2]

from cgi import escape
import time

from AccessControl.Permissions import change_versions
from AccessControl.Permissions import join_leave_versions
from AccessControl.Permissions import save_discard_version_changes
from AccessControl.Permissions import view_management_screens
from AccessControl.Role import RoleManager
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from App.class_init import default__class_init__ as InitializeClass
from App.Dialogs import MessageDialog
from App.special_dtml import DTMLFile
from App.special_dtml import HTML
from OFS.SimpleItem import Item
from Persistence import Persistent
from OFS.ObjectManager import BeforeDeleteException
import transaction

class VersionException(BeforeDeleteException):
    pass

manage_addVersionForm = DTMLFile('dtml/versionAdd', globals())

def manage_addVersion(self, id, title, REQUEST=None):
    """ """
    id=str(id)
    title=str(title)
    self=self.this()
    self._setObject(id, Version(id,title,REQUEST))
    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')

class Version(Persistent,Implicit,RoleManager,Item):
    """ """
    meta_type='Version'

    security = ClassSecurityInfo()
    security.declareObjectProtected(view_management_screens)

    manage_options=(
        (
        {'label':'Join/Leave', 'action':'manage_main',
         'help':('OFSP','Version_Join-Leave.stx')},
        {'label':'Save/Discard', 'action':'manage_end',
         'help':('OFSP','Version_Save-Discard.stx')},
        {'label':'Properties', 'action':'manage_editForm',
         'help':('OFSP','Version_Properties.stx')},
        )
        +RoleManager.manage_options
        +Item.manage_options
        )

    security.declareProtected(view_management_screens, 'manage')

    cookie=''

    index_html=None # Ugh.

    def __init__(self, id, title, REQUEST):
        self.id=id
        self.title=title

    security.declareProtected(join_leave_versions, 'manage_main')
    manage_main = DTMLFile('dtml/version', globals())

    security.declareProtected(save_discard_version_changes, 'manage_end')
    manage_end = DTMLFile('dtml/versionEnd', globals())

    security.declareProtected(view_management_screens, 'manage_editForm')
    manage_editForm = DTMLFile('dtml/versionEdit', globals())

    def _getVersionBaseCookie(self):
        import Globals  # for data
        versionbase = getattr(Globals, 'VersionBase', {})
        return versionbase.get(self.cookie)

    def title_and_id(self):
        r = Version.inheritedAttribute('title_and_id')(self)
        try:
            db = self._p_jar.db()
        except:
            # BoboPOS 2
            vbc = self._getVersionBaseCookie()
            if vbc and vbc.nonempty():
                return '%s *' % r
        else:
            # ZODB 3
            if not db.versionEmpty(self.cookie):
                return '%s *' % r

        return r

    def om_icons(self):
        """Return a list of icon URLs to be displayed by an ObjectManager"""
        return ({'path': 'misc_/OFSP/version.gif',
                  'alt': self.meta_type, 'title': self.meta_type},
                 {'path': 'misc_/PageTemplates/exclamation.gif',
                          'alt': 'Deprecated object',
                          'title': 'Version objects are deprecated '
                                   'and should not be used anyore.'},)

    security.declareProtected(change_versions, 'manage_edit')
    def manage_edit(self, title, REQUEST=None):
        """ """
        self.title=title
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    security.declareProtected(join_leave_versions, 'enter')
    def enter(self, REQUEST, RESPONSE):
        """Begin working in a version.
        """
        import Globals  # for data
        RESPONSE.setCookie(
            Globals.VersionNameName, self.cookie,
            path=(REQUEST['BASEPATH1'] or '/'),
            )
        if (REQUEST.has_key('SERVER_SOFTWARE') and
            REQUEST['SERVER_SOFTWARE'][:9]=='Microsoft'):
            # IIS doesn't handle redirect headers correctly
            return MessageDialog(
                action=REQUEST['URL1']+'/manage_main',
                message=('If cookies are enabled by your browser, then '
                         'you should have joined version %s.'
                         % escape(self.id))
                )
        return RESPONSE.redirect(REQUEST['URL1']+'/manage_main')

    security.declareProtected(join_leave_versions, 'leave')
    def leave(self, REQUEST, RESPONSE):
        """Temporarily stop working in a version
        """
        import Globals  # for data
        RESPONSE.setCookie(
            Globals.VersionNameName,'No longer active',
            expires="Mon, 25-Jan-1999 23:59:59 GMT",
            path=(REQUEST['BASEPATH1'] or '/'),
            )
        if (REQUEST.has_key('SERVER_SOFTWARE') and
            REQUEST['SERVER_SOFTWARE'][:9]=='Microsoft'):
            # IIS doesn't handle redirect headers correctly
            return MessageDialog(
                action=REQUEST['URL1']+'/manage_main',
                message=('If cookies are enabled by your browser, then '
                         'you should have left version %s.'
                         % escape(self.id))
                )
        return RESPONSE.redirect(REQUEST['URL1']+'/manage_main')

    security.declareProtected(join_leave_versions, 'leave_another')
    def leave_another(self, REQUEST, RESPONSE):
        """Leave a version that may not be the current version"""
        return self.leave(REQUEST, RESPONSE)

    security.declareProtected(save_discard_version_changes, 'save')
    def save(self, remark, REQUEST=None):
        """Make version changes permanent"""
        try:
            db = self._p_jar.db()
        except:
            # BoboPOS 2
            vbc = self._getVersionBaseCookie()
            if vbc:
                vbc.commit(remark)
        else:
            # ZODB 3
            s=self.cookie
            d=self._p_jar.getVersion()
            if d==s: d=''
            transaction.get().note(remark)
            db.commitVersion(s, d)

        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(REQUEST['URL1']+'/manage_main')

    security.declareProtected(save_discard_version_changes, 'discard')
    def discard(self, remark='', REQUEST=None):
        'Discard changes made during the version'
        try:
            db = self._p_jar.db()
        except:
            # BoboPOS 2
            vbc = self._getVersionBaseCookie()
            if vbc:
                vbc.abort()
        else:
            # ZODB 3
            transaction.get().note(remark)
            db.abortVersion(self.cookie)

        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(REQUEST['URL1']+'/manage_main')

    def nonempty(self):
        try:
            db = self._p_jar.db()
        except:
            # BoboPOS 2
            vbc = self._getVersionBaseCookie()
            return vbc and vbc.nonempty()
        else:
            # ZODB 3
            return not db.versionEmpty(self.cookie)

    # Prevent copy/move/rename of versions. It's better that way, really.

    def _canCopy(self, op=0):
        return 0

    def manage_afterClone(self, item):
        self.cookie=''

    def manage_afterAdd(self, item, container):
        if not self.cookie:
            # Physical path
            self.cookie='/'.join(self.getPhysicalPath())

    def manage_beforeDelete(self, item, container):
        import Globals  # for data
        if self.nonempty():
            raise VersionException(
                'Attempt to %sdelete a non-empty version.<br />' %
                ((self is not item) and 'indirectly ' or ''))

        try:
            REQUEST=self.REQUEST
        except:
            pass
        else:
            v=self.cookie
            if REQUEST.get(Globals.VersionNameName, '') == v:
                raise VersionException(
                    'An attempt was made to delete a version, %s, or an\n'
                    'object containing %s while\n working in the\n'
                    'version %s.  This would lead to a &quot;version\n'
                    'paradox&quot;.  The object containing the deleted\n'
                    'object would be locked and it would be impossible\n'
                    'to clear the lock by saving or discarding the\n'
                    'version, because the version would no longer\n'
                    'be accessable.<p>\n'
                    % (v,v,v))

InitializeClass(Version)
