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


$Id: Undo.py,v 1.11 1999/03/10 00:14:56 klm Exp $'''
__version__='$Revision: 1.11 $'[11:-2]

import Globals
from DateTime import DateTime
from string import atof, find, atoi, split, rfind

class UndoSupport:

    manage_UndoForm=Globals.HTMLFile(
        'undo', globals(),
        PrincipiaUndoBatchSize=20,
        first_transaction=0, last_transaction=20)

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
            
                

    def undoable_transactions(self, AUTHENTICATION_PATH=None,
                              first_transaction=None,
                              last_transaction=None,
                              PrincipiaUndoBatchSize=None):

        if AUTHENTICATION_PATH is None:
            path=self.REQUEST['AUTHENTICATION_PATH']
        else: path=AUTHENTICATION_PATH

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

        db=self._p_jar.db

        r=[]
        add=r.append
        h=['','']
        try:
            if Globals.Bobobase.has_key('_pack_time'):
                since=Globals.Bobobase['_pack_time']
            else: since=0
            trans_info=db.transaction_info(
                first_transaction,last_transaction,path,since=since)
            
        except: trans_info=[]

        for info in trans_info:
            while len(info) < 4: info.append('')
            [path, user] = (split(info[2],' ')+h)[:2]
            t=info[1]
            l=find(t,' ')
            if l >= 0: t=t[l:]
            add(
                {'pos': info[0],
                 'time': DateTime(atof(t)),
                 'id': info[1],
                 'identity': info[2],
                 'user': user,
                 'path': path,
                 'desc': info[3],
                 })
        return r or []
    
    def manage_undo_transactions(self, transaction_info, REQUEST=None):
        """
        """
        info=[]
        jar=self._p_jar
        db=jar.db
        for i in transaction_info:
            l=rfind(i,' ')
            oids=db.Toops( (i[:l],), atoi(i[l:]))
            jar.reload_oids(oids)

        if REQUEST is None: return

        RESPONSE=REQUEST['RESPONSE']
        RESPONSE.setStatus(302)
        RESPONSE['Location']="%s/manage_main" % REQUEST['URL1']
        return ''
                 
Globals.default__class_init__(UndoSupport)               
