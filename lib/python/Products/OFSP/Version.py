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
"""Version object"""

__version__='$Revision: 1.30 $'[11:-2]

import Globals, time
from AccessControl.Role import RoleManager
from Globals import MessageDialog
from Globals import Persistent
from Acquisition import Implicit
from OFS.SimpleItem import Item
from string import rfind
from Globals import HTML
from App.Dialogs import MessageDialog

manage_addVersionForm=Globals.HTMLFile('versionAdd', globals())

def manage_addVersion(self, id, title, REQUEST=None):
    """ """
    self._setObject(id, Version(id,title,REQUEST))
    return self.manage_main(self,REQUEST)


class Version(Persistent,Implicit,RoleManager,Item):
    """ """
    meta_type='Version'

    manage_options=({'label':'Join/Leave', 'action':'manage_main'},
                    {'label':'Properties', 'action':'manage_editForm'},
                    {'label':'Security', 'action':'manage_access'},
                   )

    __ac_permissions__=(
        ('View management screens', ('manage','manage_editForm', '')),
        ('Change Versions', ('manage_edit',)),
        ('Join/leave Versions', ('enter','leave','leave_another')),
        ('Save/discard Version changes', ('save','discard')),
        )

    def __init__(self, id, title, REQUEST):
        self.id=id
        self.title=title
        cookie=REQUEST['PATH_INFO']
        l=rfind(cookie,'/')
        if l >= 0: cookie=cookie[:l]
        self.cookie="%s/%s" % (cookie, id)

    manage=manage_main=Globals.HTMLFile('version', globals())
    manage_editForm   =Globals.HTMLFile('versionEdit', globals())

    def title_and_id(self):
        r=Version.inheritedAttribute('title_and_id')(self)
        try: db=self._jar.db()
        except:
            # BoboPOS 2        
            if Globals.VersionBase[self.cookie].nonempty(): return '%s *' % r
        else:
            # ZODB 3
            if not db.versionEmpty(self._version): return '%s *' % r
        
        return r

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
            #expires="Mon, 27-Dec-99 23:59:59 GMT",
            path=REQUEST['SCRIPT_NAME'],
            )
        if (REQUEST.has_key('SERVER_SOFTWARE') and
            REQUEST['SERVER_SOFTWARE'][:9]=='Microsoft'):
            # IIS doesn't handle redirect headers correctly
            return MessageDialog(
                action=REQUEST['URL1']+'/manage_main',
                message=('If cookies are enabled by your browser, then '
                         'you should have joined version %s.'
                         % self.id)
                )
        return RESPONSE.redirect(REQUEST['URL1']+'/manage_main')
        
    def leave(self, REQUEST, RESPONSE):
        """Temporarily stop working in a version"""
        RESPONSE.setCookie(
            Globals.VersionNameName,'No longer active',
            expires="Mon, 27-Aug-84 23:59:59 GMT",
            path=REQUEST['SCRIPT_NAME'],
            )
        if (REQUEST.has_key('SERVER_SOFTWARE') and
            REQUEST['SERVER_SOFTWARE'][:9]=='Microsoft'):
            # IIS doesn't handle redirect headers correctly
            return MessageDialog(
                action=REQUEST['URL1']+'/manage_main',
                message=('If cookies are enabled by your browser, then '
                         'you should have left version %s.'
                         % self.id)
                )
        return RESPONSE.redirect(REQUEST['URL1']+'/manage_main')
        
    def leave_another(self, REQUEST, RESPONSE):
        """Leave a version that may not be the current version"""
        return self.leave(REQUEST, RESPONSE)

    def save(self, remark, REQUEST=None):
        """Make version changes permanent"""
        try: db=self._jar.db()
        except:
            # BoboPOS 2
            Globals.VersionBase[self.cookie].commit(remark)
        else:
            # ZODB 3
            s=self.cookie
            d=self._p_jar.getVersion()
            if d==s: d=''
            db.commitVersion(s, d)

        if REQUEST: return self.manage_main(self, REQUEST)
    
    def discard(self, REQUEST=None):
        'Discard changes made during the version'
        try: db=self._jar.db()
        except:
            # BoboPOS 2
            Globals.VersionBase[self.cookie].abort()
        else:
            # ZODB 3
            db.abortVersion(self.cookie)

        if REQUEST: return self.manage_main(self, REQUEST)
        
    def nonempty(self):
        try: db=self._jar.db()
        except:
            # BoboPOS 2
            return Globals.VersionBase[self.cookie].nonempty()
        else:
            # ZODB 3
            return not db.versionEmpty(self.cookie)
    
    def _notifyOfCopyTo(self, container, isMove=0):
        if isMove and self.nonempty():
            raise 'Copy Error', (
                "You cannot copy a %s object with <b>unsaved</b> changes.\n"
                "You must <b>save</b> the changes first."
                % self.meta_type)
