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
__doc__='''short description

$Id: Undo.py,v 1.26 2001/07/05 14:08:55 brian Exp $'''
__version__='$Revision: 1.26 $'[11:-2]

import Globals, ExtensionClass
from DateTime import DateTime
from string import atof, find, atoi, split, rfind, join
from AccessControl import getSecurityManager
import base64

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
            path = join(user.aq_parent.getPhysicalPath()[1:-1], '/')
        else:
            path=''
        if path: spec['user_name']=Prefix(path)

        # We also only want to undo things done here
        opath=join(self.getPhysicalPath(),'/')
        if opath: spec['description']=Prefix(opath)

        r=Globals.UndoManager.undoInfo(
            first_transaction, last_transaction, spec)

        encode = base64.encodestring
        for d in r:
            d['time']=t=DateTime(d['time'])
            desc = d['description']
            tid=d['id']
            if desc:
                desc = split(desc)
                d1=desc[0]
                desc = join(desc[1:])
                if len(desc) > 60: desc = desc[:56]+' ...'
                tid = "%s %s %s %s" % (encode64(tid), t, d1, desc)
            else:
                tid = "%s %s" % (encode64(tid), t)
            d['id']=tid


        return r
    
    def manage_undo_transactions(self, transaction_info=(), REQUEST=None):
        """
        """
        undo=Globals.UndoManager.undo
        for tid in transaction_info:
            tid=split(tid)
            if tid:
                get_transaction().note("Undo %s" % join(tid[1:]))
                tid=decode64(tid[0])
                undo(tid)
            
        if REQUEST is None: return
        REQUEST['RESPONSE'].redirect("%s/manage_UndoForm" % REQUEST['URL1'])
        return ''
                 
Globals.default__class_init__(UndoSupport)


class Prefix:
    
    __no_side_effects__=1

    def __init__(self, path):
        self.value = len(path), path
        
    def __cmp__(self, o):
        l,v = self.value
        rval = cmp(o[:l],v)
        return rval
            


########################################################################
# Blech, need this cause binascii.b2a_base64 is too pickly

import binascii

def encode64(s, b2a=binascii.b2a_base64):
    if len(s) < 58: return b2a(s)
    r=[]; a=r.append
    for i in range(0, len(s), 57):
        a(b2a(s[i:i+57])[:-1])
    return join(r,'')

def decode64(s, a2b=binascii.a2b_base64):
    __traceback_info__=len(s), `s`
    return a2b(s+'\n')

del binascii
