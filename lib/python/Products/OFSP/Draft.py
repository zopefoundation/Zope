#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
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
    _session='/session'
    icon     ='misc_/OFSP/draft'
    meta_type='Principia Draft'

    __ac_permissions__=(
        ('Approve draft changes',
         ['manage_approve__draft__',
          'manage_Save__draft__','manage_Discard__draft__']
         ),
    )

    def __init__(self, id, baseid, PATH_INFO):
	self.id=id
	self._refid=baseid
	session=PATH_INFO
	l=rfind(session,'/')
	if l >= 0: session=session[:l]
	self._session="%s/%s" % (session, id)
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

        dself=getdraft(self, self._session)
        ref=getattr(dself.aq_parent.aq_base,dself._refid).aq_base.__of__(dself)
        if hasattr(ref, name): return dself, ref, getattr(ref, name)
        return getattr(self, name)
    
    def nonempty(self): return Globals.SessionBase[self._session].nonempty()

    manage_approve__draft__=Globals.HTMLFile('draftApprove', globals())

    def manage_Save__draft__(self, remark, REQUEST=None):
	"""Make session changes permanent"""
	Globals.SessionBase[self._session].commit(remark)
	if REQUEST:
            REQUEST['RESPONSE'].redirect(REQUEST['URL2']+'/manage_main')

    def manage_Discard__draft__(self, REQUEST=None):
	'Discard changes made during the session'
	Globals.SessionBase[self._session].abort()
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
            session=self.REQUEST['PATH_INFO']
            l=rfind(session,'/')
            if l >= 0: session=session[:l]
            self._session="%s/%s" % (session, self.id)
        finally:
          if 0:
            raise 'Copy Error', (
                "This object can only be copied through the web.<p>")

def getdraft(ob, session):
    if hasattr(ob,'aq_parent'):
        return getdraft(ob.aq_self, session).__of__(
            getdraft(ob.aq_parent, session))
    if hasattr(ob,'_p_oid'):
        ob=Globals.SessionBase[session].jar[ob._p_oid]
    return ob
