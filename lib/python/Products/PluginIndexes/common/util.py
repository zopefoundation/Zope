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
#############################################################################

__version__ = '$Id: util.py,v 1.7 2001/07/25 13:30:04 andreasjung Exp $'


import re
from types import StringType,ListType,TupleType,DictType,InstanceType
from DateTime import DateTime

SequenceTypes = (TupleType, ListType)

class parseIndexRequest:
    """
    This class provides functionality to hide the internals of a request
    send from the Catalog/ZCatalog to an index._apply_index() method.

    The class understands the following type of parameters:

    - old-style parameters where the query for an index as value inside
      the request directory where the index name is the name of the key.
      Additional parameters for an index could be passed as index+"_usage" ...


    - dictionary-style parameters specify a query for an index as 
      an entry in the request dictionary where the key corresponds to the 
      name of the index and the key is a dictionary with the parameters
      passed to the index. 

      Allowed keys of the parameter dictionary:

      'query'  - contains the query (either string, list or tuple) (required)

      other parameters depend on the the index


   - record-style parameters specify a query for an index as instance of the
     Record class. This happens usually when parameters from a web form use
     the "record" type e.g. <input type="text" name="path.query:record:string">.
     All restrictions of the dictionary-style parameters apply to the record-style
     parameters

    """    


    ParserException = 'IndexRequestParseError'

    def __init__(self, request, iid, options=[]):
        """ parse a request  from the ZPublisher and return a uniform
        datastructure back to the _apply_index() method of the index

          request -- the request dictionary send from the ZPublisher
          iid     -- Id of index
          options -- a list of options the index is interested in 
        """

        self.id = iid

        if not request.has_key(iid):
            self.keys = None
            return

        # We keep this for backward compatility
        usage_param = iid + '_usage'
        if request.has_key(usage_param):
            self.usage = request[usage_param]

        param = request[iid]
        keys = None
        t = type(param)

        if t is InstanceType and not isinstance(param, DateTime):
            """ query is of type record """

            record = param

            if not hasattr(record, 'query'):
                raise self.ParserException, (
                    "record for '%s' *must* contain a "
                    "'query' attribute" % self.id)
            keys = record.query

            if type(keys) is StringType:
                keys = [keys.strip()]

            for op in options:
                if op == "query": continue

                if hasattr(record, op):
                    setattr(self, op, getattr(record, op))

        elif t is DictType:
            """ query is a dictionary containing all parameters """
    
            query = param.get("query", ())
            if type(query) in SequenceTypes:
                keys = query
            else:
                keys = [ query ]

            for op in options:         
                if op == "query": continue

                if param.has_key(op):
                    setattr(self, op, param[op])
 
        else:
            """ query is tuple, list, string, number, or something else """

            if t in SequenceTypes:
                keys = param
            else:
                keys = [param]

            for op in options:
                field = iid + "_" + op
                if request.has_key(field):
                    setattr(self, op, request[field])

        # This was some kind of over-optimimization and broke
        # queries with ("",) to search for empty fields
        # (See Collector 2423)
        
#      if keys is not None:
#           # Filter out empty strings.
#            keys = filter(lambda key: key != '', keys)

        if not keys:
            keys = None

        self.keys = keys


    def get(self,k,default_v=None):
        
        if hasattr(self,k):
            v = getattr(self,k)
            if v: return v
            else: return default_v
        else:
            return default_v

def test():

    r  = parseIndexRequest({'path':{'query':"","level":2,"operator":'and'}},'path',['query',"level","operator"])
    for k in dir(r):
        print k,getattr(r,k)

if __name__=="__main__":
    test()
