##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
$Id$"""
__version__='$Revision: 1.34 $'[11:-2]

from Acquisition import aq_base, aq_parent, aq_inner
from AccessControl import getSecurityManager
from DateTime import DateTime
import Globals, ExtensionClass
from ZopeUndo.Prefix import Prefix
import transaction

class UndoSupport(ExtensionClass.Base):

    __ac_permissions__=(
        ('Undo changes', (
            'manage_undo_transactions',
            'undoable_transactions',
            'manage_UndoForm',
            )),
        )

    manage_options=(
        {'label':'Undo', 'action':'manage_UndoForm',
         'help':('OFSP','Undo.stx')},
        )

    manage_UndoForm=Globals.DTMLFile(
        'dtml/undo',
        globals(),
        PrincipiaUndoBatchSize=20,
        first_transaction=0,
        last_transaction=20
        )

    def get_request_var_or_attr(self, name, default):
        if hasattr(self, 'REQUEST'):
            REQUEST=self.REQUEST
            if REQUEST.has_key(name): return REQUEST[name]
            if hasattr(self, name): v=getattr(self, name)
            else: v=default
            REQUEST[name]=v
            return v
        else:
            if hasattr(self, name): v=getattr(self, name)
            else: v=default
            return v

    def undoable_transactions(self, first_transaction=None,
                              last_transaction=None,
                              PrincipiaUndoBatchSize=None):

        if first_transaction is None:
            first_transaction=self.get_request_var_or_attr(
                'first_transaction', 0)

        if PrincipiaUndoBatchSize is None:
            PrincipiaUndoBatchSize=self.get_request_var_or_attr(
                'PrincipiaUndoBatchSize', 20)

        if last_transaction is None:
            last_transaction=self.get_request_var_or_attr(
                'last_transaction',
                first_transaction+PrincipiaUndoBatchSize)

        spec={}

        # A user is allowed to undo transactions that were initiated
        # by any member of a user folder in the place where the user
        # is defined.
        user = getSecurityManager().getUser()
        if hasattr(user, 'aq_parent'):
            path = '/'.join(user.aq_parent.getPhysicalPath()[1:-1])
        else:
            path=''
        if path: spec['user_name']=Prefix(path)

        if getattr(aq_parent(aq_inner(self)), '_p_jar', None) == self._p_jar:
            # We only want to undo things done here (and not in mounted
            # databases)
            opath='/'.join(self.getPhysicalPath())
        else:
            # Special case: at the root of a database,
            # allow undo of any path.
            opath = None
        if opath: spec['description']=Prefix(opath)

        r = self._p_jar.db().undoInfo(
            first_transaction, last_transaction, spec)

        for d in r:
            d['time']=t=DateTime(d['time'])
            desc = d['description']
            tid=d['id']
            if desc:
                desc = desc.split()
                d1=desc[0]
                desc = ''.join(desc[1:])
                if len(desc) > 60: desc = desc[:56]+' ...'
                tid = "%s %s %s %s" % (encode64(tid), t, d1, desc)
            else:
                tid = "%s %s" % (encode64(tid), t)
            d['id']=tid


        return r

    def manage_undo_transactions(self, transaction_info=(), REQUEST=None):
        """
        """
        undo=self._p_jar.db().undo

        for tid in transaction_info:
            tid=tid.split()
            if tid:
                transaction.get().note("Undo %s" % ''.join(tid[1:]))
                tid=decode64(tid[0])
                undo(tid)

        if REQUEST is None: return
        REQUEST['RESPONSE'].redirect("%s/manage_UndoForm" % REQUEST['URL1'])
        return ''

Globals.default__class_init__(UndoSupport)

########################################################################
# Blech, need this cause binascii.b2a_base64 is too pickly

import binascii

def encode64(s, b2a=binascii.b2a_base64):
    if len(s) < 58: return b2a(s)
    r=[]; a=r.append
    for i in range(0, len(s), 57):
        a(b2a(s[i:i+57])[:-1])
    return ''.join(r)

def decode64(s, a2b=binascii.a2b_base64):
    __traceback_info__=len(s), `s`
    return a2b(s+'\n')

del binascii
