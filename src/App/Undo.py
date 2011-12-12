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
"""Undo support.
"""

from Acquisition import aq_inner
from Acquisition import aq_parent
from AccessControl import getSecurityManager
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import undo_changes
from App.interfaces import IUndoSupport
from App.special_dtml import DTMLFile
from DateTime.DateTime import DateTime
import ExtensionClass
import transaction
from ZopeUndo.Prefix import Prefix
from zope.interface import implements


class UndoSupport(ExtensionClass.Base):

    implements(IUndoSupport)

    security = ClassSecurityInfo()

    manage_options=(
        {'label': 'Undo', 'action': 'manage_UndoForm'},
        )

    security.declareProtected(undo_changes, 'manage_UndoForm')
    manage_UndoForm = DTMLFile(
        'dtml/undo',
        globals(),
        PrincipiaUndoBatchSize=20,
        first_transaction=0,
        last_transaction=20,
        )

    def _get_request_var_or_attr(self, name, default):
        if hasattr(self, 'REQUEST'):
            REQUEST=self.REQUEST
            if REQUEST.has_key(name):
                return REQUEST[name]
            if hasattr(self, name):
                v = getattr(self, name)
            else:
                v = default
            REQUEST[name] = v
            return v
        else:
            if hasattr(self, name):
                v = getattr(self, name)
            else:
                v = default
            return v

    security.declareProtected(undo_changes, 'undoable_transactions')
    def undoable_transactions(self, first_transaction=None,
                              last_transaction=None,
                              PrincipiaUndoBatchSize=None):

        if first_transaction is None:
            first_transaction = self._get_request_var_or_attr(
                'first_transaction', 0)

        if PrincipiaUndoBatchSize is None:
            PrincipiaUndoBatchSize = self._get_request_var_or_attr(
                'PrincipiaUndoBatchSize', 20)

        if last_transaction is None:
            last_transaction = self._get_request_var_or_attr(
                'last_transaction',
                first_transaction+PrincipiaUndoBatchSize)

        spec = {}

        # A user is allowed to undo transactions that were initiated
        # by any member of a user folder in the place where the user
        # is defined.
        user = getSecurityManager().getUser()
        user_parent = aq_parent(user)
        if user_parent is not None:
            path = '/'.join(user_parent.getPhysicalPath()[1:-1])
        else:
            path = ''
        if path:
            spec['user_name'] = Prefix(path)

        if getattr(aq_parent(aq_inner(self)), '_p_jar', None) == self._p_jar:
            # We only want to undo things done here (and not in mounted
            # databases)
            opath = '/'.join(self.getPhysicalPath())
        else:
            # Special case: at the root of a database,
            # allow undo of any path.
            opath = None
        if opath:
            spec['description'] = Prefix(opath)

        r = self._p_jar.db().undoInfo(
            first_transaction, last_transaction, spec)

        for d in r:
            d['time'] = t = DateTime(d['time'])
            desc = d['description']
            tid = d['id']
            if desc:
                desc = desc.split()
                d1 = desc[0]
                desc = ' '.join(desc[1:])
                if len(desc) > 60:
                    desc = desc[:56] + ' ...'
                tid = "%s %s %s %s" % (encode64(tid), t, d1, desc)
            else:
                tid = "%s %s" % (encode64(tid), t)
            d['id'] = tid

        return r

    security.declareProtected(undo_changes, 'manage_undo_transactions')
    def manage_undo_transactions(self, transaction_info=(), REQUEST=None):
        """
        """
        tids = []
        descriptions = []
        for tid in transaction_info:
            tid = tid.split()
            if tid:
                tids.append(decode64(tid[0]))
                descriptions.append(tid[-1])

        if tids:
            transaction.get().note("Undo %s" % ' '.join(descriptions))
            self._p_jar.db().undoMultiple(tids)

        if REQUEST is None:
            return
        REQUEST['RESPONSE'].redirect("%s/manage_UndoForm" % REQUEST['URL1'])
        return ''

InitializeClass(UndoSupport)

########################################################################
# Blech, need this cause binascii.b2a_base64 is too pickly

import binascii


def encode64(s, b2a=binascii.b2a_base64):
    if len(s) < 58:
        return b2a(s)
    r = []
    a = r.append
    for i in range(0, len(s), 57):
        a(b2a(s[i:i+57])[:-1])
    return ''.join(r)


def decode64(s, a2b=binascii.a2b_base64):
    __traceback_info__=len(s), `s`
    return a2b(s+'\n')

del binascii
