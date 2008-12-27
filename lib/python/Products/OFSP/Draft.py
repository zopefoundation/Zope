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
from AccessControl.SecurityInfo import ClassSecurityInfo
import AccessControl.User
from App.class_init import default__class_init__ as InitializeClass
from App.special_dtml import HTMLFile
from Acquisition import Implicit
from OFS import SimpleItem
from Persistence import Persistent

manage_addPrincipiaDraftForm = HTMLFile('dtml/draftAdd',globals())
def manage_addPrincipiaDraft(self, id, baseid, PATH_INFO, REQUEST=None):
    "Add a draft object"
    self._setObject(id, Draft(id, baseid, PATH_INFO))
    if REQUEST is not None: return self.manage_main(self,REQUEST)

class Draft(Persistent, Implicit, SimpleItem.Item):
    "Daft objects"
    _refid=''
    _version='/version'
    meta_type='Zope Draft'

    security = ClassSecurityInfo()

    def __init__(self, id, baseid, PATH_INFO):
        self.id=id
        self._refid=baseid
        version=PATH_INFO
        l=version.rfind('/')
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


    def _getVersionBase(self):
        import Globals  # for data
        versionbase = getattr(Globals, 'VersionBase', {})
        return versionbase.get(self._version)

    def _bobo_traverse__(self, REQUEST, name):
        if name[-9:]=='__draft__': return getattr(self, name)


        try:
            db = self._p_jar.db()
        except:
            # BoboPOS 2
            vb = self._getVersionBase()
            jar = vb and vb.jar
        else:
            # ZODB 3
            jar = db.open(self._version)
            cleanup = Cleanup(jar)
            REQUEST[Cleanup]=cleanup

        dself=getdraft(self, jar)

        ref=getattr(dself.aq_parent.aq_base,dself._refid).aq_base.__of__(dself)
        if hasattr(ref, name): return dself, ref, getattr(ref, name)
        return getattr(self, name)

    def nonempty(self):
        try: db=self._p_jar.db()
        except:
            # BoboPOS 2
            vb = self._getVersionBase()
            return vb and vb.nonempty()
        else:
            # ZODB 3
            return not db.versionEmpty(self._version)

    security.declareProtected('Approve draft changes',
                              'manage_approve__draft__')
    manage_approve__draft__ = HTMLFile('dtml/draftApprove', globals())

    security.declareProtected('Approve draft changes',
                              'manage_Save__draft__')
    def manage_Save__draft__(self, remark, REQUEST=None):
        """Make version changes permanent"""
        try: db=self._p_jar.db()
        except:
            # BoboPOS 2
            vb = self._getVersionBase()
            vb.commit(remark)
        else:
            # ZODB 3
            s=self._version
            d=self._p_jar.getVersion()
            if d==s: d=''
            db.commitVersion(s, d)

        if REQUEST:
            REQUEST['RESPONSE'].redirect(REQUEST['URL2']+'/manage_main')

    security.declareProtected('Approve draft changes',
                              'manage_Discard__draft__')
    def manage_Discard__draft__(self, REQUEST=None):
        'Discard changes made during the version'
        try: db=self._p_jar.db()
        except:
            # BoboPOS 2
            vb = self._getVersionBase()
            vb.abort()
        else:
            # ZODB 3
            db.abortVersion(self._version)

        if REQUEST:
            REQUEST['RESPONSE'].redirect(REQUEST['URL2']+'/manage_main')

    def manage_afterClone(self, item):
        self._version=''

    def manage_afterAdd(self, item, container):
        if not self._version:
            self._version=self.absolute_url(1)

    def manage_beforeDelete(self, item, container):
        if self.nonempty():
            raise ValueError, (
                'Attempt to %sdelete a non-empty version.<p>'
                ((self is not item) and 'indirectly ' or ''))

InitializeClass(Draft)


def getdraft(ob, jar):

    if hasattr(ob,'aq_parent'):
        return getdraft(ob.aq_self, jar).__of__(getdraft(ob.aq_parent, jar))

    if hasattr(ob,'_p_oid'): ob=jar[ob._p_oid]

    return ob


class Cleanup:
    def __init__(self, jar):
        self._jar = jar

    def __del__(self):
        self._jar.close()
