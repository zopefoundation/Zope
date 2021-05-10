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

import binascii

import transaction
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import undo_changes
from Acquisition import Implicit
from App.Management import Tabs
from App.special_dtml import DTMLFile
from DateTime.DateTime import DateTime


class UndoSupport(Tabs, Implicit):

    security = ClassSecurityInfo()

    manage_options = (
        {'label': 'Undo', 'action': 'manage_UndoForm'},
    )

    security.declareProtected(undo_changes, 'manage_UndoForm')  # NOQA: D001
    manage_UndoForm = DTMLFile(
        'dtml/undo',
        globals(),
        PrincipiaUndoBatchSize=20,
        first_transaction=0,
        last_transaction=20,
    )

    def _get_request_var_or_attr(self, name, default):
        if hasattr(self, 'REQUEST'):
            REQUEST = self.REQUEST
            if name in REQUEST:
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

    @security.protected(undo_changes)
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
                first_transaction + PrincipiaUndoBatchSize)

        r = self._p_jar.db().undoInfo(first_transaction, last_transaction)

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
                tid = f"{encode64(tid)} {t} {d1} {desc}"
            else:
                tid = f"{encode64(tid)} {t}"
            d['id'] = tid

        return r

    @security.protected(undo_changes)
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
            ts = transaction.get()
            ts.note("Undo %s" % ' '.join(descriptions))
            self._p_jar.db().undoMultiple(tids)
            try:
                ts.commit()
            except Exception as exc:
                if REQUEST is None:
                    raise

                ts.abort()
                error = '{}: {}'.format(exc.__class__.__name__, str(exc))
                return self.manage_UndoForm(self, REQUEST,
                                            manage_tabs_message=error,
                                            manage_tabs_type='danger')

        if REQUEST is not None:
            REQUEST.RESPONSE.redirect("%s/manage_UndoForm" % REQUEST['URL1'])


InitializeClass(UndoSupport)

# Blech, need this cause binascii.b2a_base64 is too pickly


def encode64(s, b2a=binascii.b2a_base64):
    if len(s) < 58:
        return b2a(s).decode('ascii')
    r = []
    a = r.append
    for i in range(0, len(s), 57):
        a(b2a(s[i:i + 57])[:-1])
    return (b''.join(r)).decode('ascii')


def decode64(s, a2b=binascii.a2b_base64):
    __traceback_info__ = len(s), repr(s)
    return a2b(s + '\n')
