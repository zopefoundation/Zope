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

import Globals, time
from AccessControl.Role import RoleManager
from Globals import MessageDialog
from Globals import Persistent
from Acquisition import Implicit
from OFS.SimpleItem import Item
from Globals import HTML
from App.Dialogs import MessageDialog
from OFS.ObjectManager import BeforeDeleteException
from cgi import escape

import transaction

class VersionException(BeforeDeleteException): pass

manage_addVersionForm=Globals.DTMLFile('dtml/versionAdd', globals())

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

    __ac_permissions__=(
        ('View management screens', ('manage','manage_editForm', '')),
        ('Change Versions', ('manage_edit',)),
        ('Join/leave Versions',
         ('manage_main', 'enter','leave','leave_another')),
        ('Save/discard Version changes',
         ('manage_end', 'save','discard')),
        )

    cookie=''

    index_html=None # Ugh.

    def __init__(self, id, title, REQUEST):
        self.id=id
        self.title=title

    manage_main=Globals.DTMLFile('dtml/version', globals())
    manage_end=Globals.DTMLFile('dtml/versionEnd', globals())
    manage_editForm   =Globals.DTMLFile('dtml/versionEdit', globals())

    def title_and_id(self):
        r=Version.inheritedAttribute('title_and_id')(self)
        try: db=self._p_jar.db()
        except:
            # BoboPOS 2
            if Globals.VersionBase[self.cookie].nonempty(): return '%s *' % r
        else:
            # ZODB 3
            if not db.versionEmpty(self.cookie): return '%s *' % r

        return r

    def om_icons(self):
        """Return a list of icon URLs to be displayed by an ObjectManager"""
        return ({'path': 'misc_/OFSP/version.gif',
                  'alt': self.meta_type, 'title': self.meta_type},
                 {'path': 'misc_/PageTemplates/exclamation.gif',
                          'alt': 'Deprecated object',
                          'title': 'Version objects are deprecated and should not be used anyore.'},)

    def manage_edit(self, title, REQUEST=None):
        """ """
        self.title=title
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    def enter(self, REQUEST, RESPONSE):
        """Begin working in a version"""
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

    def leave(self, REQUEST, RESPONSE):
        """Temporarily stop working in a version"""
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

    def leave_another(self, REQUEST, RESPONSE):
        """Leave a version that may not be the current version"""
        return self.leave(REQUEST, RESPONSE)

    def save(self, remark, REQUEST=None):
        """Make version changes permanent"""
        try: db=self._p_jar.db()
        except:
            # BoboPOS 2
            Globals.VersionBase[self.cookie].commit(remark)
        else:
            # ZODB 3
            s=self.cookie
            d=self._p_jar.getVersion()
            if d==s: d=''
            transaction.get().note(remark)
            db.commitVersion(s, d)

        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(REQUEST['URL1']+'/manage_main')

    def discard(self, remark='', REQUEST=None):
        'Discard changes made during the version'
        try: db=self._p_jar.db()
        except:
            # BoboPOS 2
            Globals.VersionBase[self.cookie].abort()
        else:
            # ZODB 3
            transaction.get().note(remark)
            db.abortVersion(self.cookie)

        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(REQUEST['URL1']+'/manage_main')

    def nonempty(self):
        try: db=self._p_jar.db()
        except:
            # BoboPOS 2
            return Globals.VersionBase[self.cookie].nonempty()
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
        if self.nonempty():
            raise VersionException(
                'Attempt to %sdelete a non-empty version.<br />' %
                ((self is not item) and 'indirectly ' or ''))

        try: REQUEST=self.REQUEST
        except: pass
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
