##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################
"""Session object"""

__version__='$Revision: 1.24 $'[11:-2]

import Globals, time
from AccessControl.Role import RoleManager
from Globals import MessageDialog
from Globals import Persistent
from Acquisition import Implicit
from OFS.SimpleItem import Item
from string import rfind
from Globals import HTML
from App.Dialogs import MessageDialog

manage_addSessionForm=Globals.HTMLFile('sessionAdd', globals())

def manage_addSession(self, id, title, REQUEST=None):
    """ """
    self._setObject(id, Session(id,title,REQUEST))
    return self.manage_main(self,REQUEST)


class Session(Persistent,Implicit,RoleManager,Item):
    """ """
    meta_type='Session'
    icon     ='misc_/OFSP/session'

    manage_options=({'label':'Join/Leave', 'action':'manage_main'},
                    {'label':'Properties', 'action':'manage_editForm'},
                    {'label':'Security', 'action':'manage_access'},
                   )

    __ac_permissions__=(
    ('View management screens', ['manage','manage_tabs','manage_editForm', '']),
    ('Change permissions', ['manage_access']),
    ('Change Sessions', ['manage_edit']),
    ('Join/leave Sessions', ['enter','leave','leave_another']),
    ('Save/discard Session changes', ['save','discard']),
    )

    def __init__(self, id, title, REQUEST):
        self.id=id
        self.title=title
        cookie=REQUEST['PATH_INFO']
        l=rfind(cookie,'/')
        if l >= 0: cookie=cookie[:l]
        self.cookie="%s/%s" % (cookie, id)

    manage=manage_main=Globals.HTMLFile('session', globals())
    manage_editForm   =Globals.HTMLFile('sessionEdit', globals())

    def title_and_id(self):
        r=Session.inheritedAttribute('title_and_id')(self)
        if Globals.SessionBase[self.cookie].nonempty(): return '%s *' % r
        return r

    def manage_edit(self, title, REQUEST=None):
        """ """
        self.title=title
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    def enter(self, REQUEST, RESPONSE):
        """Begin working in a session"""
        RESPONSE.setCookie(
            Globals.SessionNameName, self.cookie,
            #expires="Mon, 27-Dec-99 23:59:59 GMT",
            path=REQUEST['SCRIPT_NAME'],
            )
        if (REQUEST.has_key('SERVER_SOFTWARE') and
            REQUEST['SERVER_SOFTWARE'][:9]=='Microsoft'):
            # IIS doesn't handle redirect headers correctly
            return MessageDialog(
                action=REQUEST['URL1']+'/manage_main',
                message=('If cookies are enabled by your browser, then '
                         'you should have joined session %s.'
                         % self.id)
                )
        return RESPONSE.redirect(REQUEST['URL1']+'/manage_main')
        
    def leave(self, REQUEST, RESPONSE):
        """Temporarily stop working in a session"""
        RESPONSE.setCookie(
            Globals.SessionNameName,'No longer active',
            expires="Mon, 27-Aug-84 23:59:59 GMT",
            path=REQUEST['SCRIPT_NAME'],
            )
        if (REQUEST.has_key('SERVER_SOFTWARE') and
            REQUEST['SERVER_SOFTWARE'][:9]=='Microsoft'):
            # IIS doesn't handle redirect headers correctly
            return MessageDialog(
                action=REQUEST['URL1']+'/manage_main',
                message=('If cookies are enabled by your browser, then '
                         'you should have left session %s.'
                         % self.id)
                )
        return RESPONSE.redirect(REQUEST['URL1']+'/manage_main')
        
    def leave_another(self, REQUEST, RESPONSE):
        """Leave a session that may not be the current session"""
        return self.leave(REQUEST, RESPONSE)

    def save(self, remark, REQUEST=None):
        """Make session changes permanent"""
        Globals.SessionBase[self.cookie].commit(remark)
        if REQUEST: return self.manage_main(self, REQUEST)
    
    def discard(self, REQUEST=None):
        'Discard changes made during the session'
        Globals.SessionBase[self.cookie].abort()
        if REQUEST: return self.manage_main(self, REQUEST)
        
    def nonempty(self): return Globals.SessionBase[self.cookie].nonempty()
    
    def _notifyOfCopyTo(self, container, isMove=0):
        if isMove and self.nonempty():
            raise 'Copy Error', (
                "You cannot copy a %s object with <b>unsaved</b> changes.\n"
                "You must <b>save</b> the changes first."
                % self.meta_type)
