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
import Globals, AccessControl.User
from Globals import Persistent
from Acquisition import Implicit
from OFS import SimpleItem
from string import rfind

manage_addPrincipiaDraftForm=Globals.HTMLFile('draftAdd',globals())
def manage_addPrincipiaDraft(self, id, baseid, PATH_INFO, REQUEST=None):
    "Add a draft object"
    self._setObject(id, Draft(id, baseid, PATH_INFO))
    if REQUEST is not None: return self.manage_main(self,REQUEST)

class Draft(Persistent, Implicit, SimpleItem.Item):
    "Daft objects"
    _refid=''
    _version='/version'
    meta_type='Zope Draft'

    __ac_permissions__=(
        ('Approve draft changes',
         ('manage_approve__draft__',
          'manage_Save__draft__','manage_Discard__draft__')
         ),
    )

    def __init__(self, id, baseid, PATH_INFO):
        self.id=id
        self._refid=baseid
        version=PATH_INFO
        l=rfind(version,'/')
        if l >= 0: version=version[:l]
        self._version="%s/%s" % (version, id)
        self.users__draft__=uf=AccessControl.User.UserFolder()
        self.__allow_groups__=uf
    
    def icon(self):
        try: return getattr(self.aq_parent.aq_base,self._refid).icon
        except: return 'p_/broken'

    def manage_options(self):
        try: return getattr(self.aq_parent.aq_base,self._refid).manage_options
        except: return ()

    def title(self):
        return 'draft of '+self._refid

    def title_and_id(self):
        nonempty=self.nonempty()
        if nonempty:
            return ('draft of %s (%s)'
                    '</a> <a href="%s/users__draft__/manage_main">[Users]'
                    '</a> <a href="%s/manage_approve__draft__">[Approve]'
                    % (self._refid, self.id,
                       self.id,
                       self.id,
                       ))
        else:
            return ('draft of %s (%s)'
                    '</a> <a href="%s/users__draft__/manage_main">[Users]'
                    % (self._refid, self.id,
                       self.id,
                       ))

    def __bobo_traverse__(self, REQUEST, name):
        if name[-9:]=='__draft__': return getattr(self, name)

        dself=getdraft(self, self._version)
        ref=getattr(dself.aq_parent.aq_base,dself._refid).aq_base.__of__(dself)
        if hasattr(ref, name): return dself, ref, getattr(ref, name)
        return getattr(self, name)
    
    def nonempty(self): return Globals.VersionBase[self._version].nonempty()

    manage_approve__draft__=Globals.HTMLFile('draftApprove', globals())

    def manage_Save__draft__(self, remark, REQUEST=None):
        """Make version changes permanent"""
        Globals.VersionBase[self._version].commit(remark)
        if REQUEST:
            REQUEST['RESPONSE'].redirect(REQUEST['URL2']+'/manage_main')

    def manage_Discard__draft__(self, REQUEST=None):
        'Discard changes made during the version'
        Globals.VersionBase[self._version].abort()
        if REQUEST:
            REQUEST['RESPONSE'].redirect(REQUEST['URL2']+'/manage_main')

    def _notifyOfCopyTo(self, container, isMove=0):
        if isMove and self.nonempty():
            raise 'Copy Error', (
                "You cannot copy a %s object with <b>unapproved</b> changes.\n"
                "You must <b>approve</b> the changes first."
                % self.meta_type)

    def _postCopy(self, container, op=0):

        try: 
            version=self.REQUEST['PATH_INFO']
            l=rfind(version,'/')
            if l >= 0: version=version[:l]
            self._version="%s/%s" % (version, self.id)
        finally:
          if 0:
            raise 'Copy Error', (
                "This object can only be copied through the web.<p>")

def getdraft(ob, version):
    if hasattr(ob,'aq_parent'):
        return getdraft(ob.aq_self, version).__of__(
            getdraft(ob.aq_parent, version))
    if hasattr(ob,'_p_oid'):
        ob=Globals.VersionBase[version].jar[ob._p_oid]
    return ob
