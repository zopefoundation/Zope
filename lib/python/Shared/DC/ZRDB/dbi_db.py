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


$Id: dbi_db.py,v 1.7 1999/03/10 00:15:44 klm Exp $'''
#     Copyright 
#
#       Copyright 1997 Digital Creations, Inc, 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved. 
# 
__version__='$Revision: 1.7 $'[11:-2]

import string, sys
from string import strip, split, find, join

failures=0
calls=0

nonselect_desc=[
    ('Query',  'STRING', 62, 62, 0, 0, 1),
    ('Status', 'STRING', 12, 12, 0, 0, 1),
    ('Calls',  'STRING', 12, 12, 0, 0, 1),
    ]

class DB:

    _p_oid=_p_changed=_registered=None

    defs={'STRING':'s', 'NUMBER':'n', 'DATE':'d'}

    def Database_Connection(self, string):
        # Create a dbi-compatible database connection
        raise 'ImplementedBySubclass', (
            'attempt to create a database connection for an abstract dbi')

    Database_Error='Should be overriden by subclass'

    def __init__(self,connection):
        self.connection=connection
        db=self.db=self.Database_Connection(connection)
        self.cursor=db.cursor()
        
    def str(self,v, StringType=type('')):
        if v is None: return ''
        r=str(v)
        if r[-1:]=='L' and type(v) is not StringType: r=r[:-1]
        return r

    def __inform_commit__(self, *ignored):
        self._registered=None
        self.db.commit()

    def __inform_abort__(self, *ignored):
        self._registered=None
        self.db.rollback()

    def register(self):
        if self._registered: return
        get_transaction().register(self)
        self._registered=1
        

    def query(self,query_string, max_rows=9999999):
        global failures, calls
        calls=calls+1
        try:
            c=self.cursor
            self.register()
            queries=filter(None, map(strip,split(query_string, '\0')))
            if not queries: raise 'Query Error', 'empty query'
            if len(queries) > 1:
                result=[]
                for qs in queries:
                    r=c.execute(qs)
                    if r is None: raise 'Query Error', (
                        'select in multiple sql-statement query'
                        )
                    result.append((qs, str(`r`), calls))
                desc=nonselect_desc
            else:
                query_string=queries[0]
                r=c.execute(query_string)
                if r is None:
                    result=c.fetchmany(max_rows)
                    desc=c.description
                else:
                    result=((query_string, str(`r`), calls),)
                    desc=nonselect_desc
            failures=0
            c.close()
        except self.Database_Error, mess:
            c.close()
            self.db.rollback()
            failures=failures+1
            if ((find(mess,": invalid") < 0 and
                 find(mess,"PARSE") < 0) or
                # DBI IS stupid
                find(mess,
                     "Error while trying to retrieve text for error") > 0
                or
                # If we have a large number of consecutive failures,
                # our connection is probably dead.
                failures > 100
                ):
                # Hm. maybe the db is hosed.  Let's try once to restart it.
                failures=0
                c.close()
                self.db.close()
                db=self.db=self.Database_Connection(self.connection)
                self.cursor=db.cursor()
                c=self.cursor
                c.execute(query_string)
                result=c.fetchall()
                desc=c.description
            else: raise sys.exc_type, sys.exc_value, sys.exc_traceback
        
        if result:
            result=join(
                    map(
                        lambda row, self=self:
                        join(map(self.str,row),'\t'),
                        result),
                    '\n')+'\n'
        else:
            result=''

        return (
            "%s\n%s\n%s" % (
                join(map(lambda d: d[0],desc), '\t'),
                join(
                    map(
                        lambda d, defs=self.defs: "%d%s" % (d[2],defs[d[1]]),
                        desc),
                    '\t'),
                result,
                )
            )
