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

__version__='$Revision: 1.44 $'[11:-2]

import Globals, time
from AccessControl.Role import RoleManager
from Globals import MessageDialog
from Globals import Persistent
from Acquisition import Implicit
from OFS.SimpleItem import Item
from string import rfind, join
from Globals import HTML
from App.Dialogs import MessageDialog
from OFS.ObjectManager import BeforeDeleteException

class VersionException(BeforeDeleteException): pass

manage_addVersionForm=Globals.HTMLFile('versionAdd', globals())

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

    manage_main=Globals.HTMLFile('version', globals())
    manage_end=Globals.HTMLFile('versionEnd', globals())
    manage_editForm   =Globals.HTMLFile('versionEdit', globals())

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
            expires="Mon, 25-Jan-1999 23:59:59 GMT",
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
        try: db=self._p_jar.db()
        except:
            # BoboPOS 2
            Globals.VersionBase[self.cookie].commit(remark)
        else:
            # ZODB 3
            s=self.cookie
            d=self._p_jar.getVersion()
            if d==s: d=''
            get_transaction().note(remark)
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
            get_transaction().note(remark)
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
            # Site-relative, quoted
            self.cookie=join(self.getPhysicalPath(),'/')

    def manage_beforeDelete(self, item, container):        
        if self.nonempty():
            raise VersionException(
                'Attempt to %sdelete a non-empty version.<p>'
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

