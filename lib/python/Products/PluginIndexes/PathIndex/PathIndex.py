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

__version__ = '$Id: PathIndex.py,v 1.7 2001/10/03 13:04:06 andreasjung Exp $'

from Products.PluginIndexes import PluggableIndex 
from Products.PluginIndexes.common.util import parseIndexRequest

from Globals import Persistent, DTMLFile
from Acquisition import Implicit
from OFS.History import Historical
from OFS.SimpleItem import SimpleItem

from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree,OOSet
from BTrees.OIBTree import OIBTree
from BTrees.IIBTree import IISet,difference,intersection,union
from types import StringType, ListType, TupleType
import re,warnings


class PathIndex(PluggableIndex.PluggableIndex, Persistent,
    Implicit, SimpleItem):
    """ A path index stores all path components of the physical 
    path of an object: 

    Internal datastructure:

    - a physical path of an object is split into its components
  
    - every component is kept as a  key of a OOBTree in self._indexes

    - the value is a mapping 'level of the path component' to
      'all documentIds with this path component on this level'
  
    """

    __implements__ = (PluggableIndex.PluggableIndexInterface,)

    meta_type="PathIndex"
    
    manage_options= (
        {'label': 'Settings',     
         'action': 'manage_main',
         'help': ('PathIndex','PathIndex_Settings.stx')},
    )

    query_options = ["query","level"]


    def __init__(self,id,caller=None):
        self.id = id

        # experimental code for specifing the operator
        self.operators = ['or','and'] 
        self.useOperator = 'or'

        self.clear()


    def clear(self):
        """ clear everything """

        self._depth   = 0 
        self._index   = OOBTree()
        self._unindex = IOBTree()


    def insertEntry(self,comp,id,level):
        """ 
        k is a path component (generated by splitPath() )
        v is the documentId
        level is the level of the component inside the path
        """

        if self._index.has_key(comp)==0:
            self._index[comp] = IOBTree()

        if self._index[comp].has_key(level)==0:
            self._index[comp][level] = IISet()

        self._index[comp][level].insert(id)
        
        if level > self._depth: self._depth = level

        # reverse index
        if not self._unindex.has_key(id):
            self._unindex[id] = OOSet()
        self._unindex[id].insert( (comp,level) )
            

    def index_object(self, documentId, obj ,threshold=100):
        """ hook for (Z)Catalog """


        # first we check if the object provide an attribute or
        # method to be used as hook for the PathIndex

        if hasattr(obj,self.id):
            f = getattr(obj,self.id)
            if callable(f):
                path = f()
            else:
                path = f
        else:             

            try:
                path = obj.getPhysicalPath()
            except:
                return 0

        if type(path) in (ListType,TupleType):
            path = '/'+ '/'.join(path[1:])

        comps = self.splitPath(path,obj)

        if obj.meta_type != 'Folder':
            comps = comps[:-1]

        for i in range(len(comps)):
            self.insertEntry( comps[i],documentId,i)

        return 1


    def unindex_object(self,id):
        """ hook for (Z)Catalog """

        if not self._unindex.has_key(id):
            return 

        for comp,level in self._unindex[id]:

            self._index[comp][level].remove(id)

            if len(self._index[comp][level])==0:
                del self._index[comp][level]

            if len(self._index[comp])==0:
                del self._index[comp]

        del self._unindex[id]


    def printIndex(self):
        for k,v in self._index.items():
            print "-"*78
            print k
            for k1,v1 in v.items():
                print k1,v1,

            print 
            

    def splitPath(self,path,obj=None):
        """ split physical path of object. If the object has
        as function splitPath() we use this user-defined function
        to split the path
        """

        if hasattr(obj,"splitPath"):
            comps = obj.splitPath(path)
        else:
            comps = filter(lambda x: x , re.split("/",path))

        return comps


    def search(self,path,default_level=0):
        """
        path is either a string representing a
        relative URL or a part of a relative URL or
        a tuple (path,level).

        level>=0  starts searching at the given level
        level<0   not implemented yet
        """       

        if isinstance(path,StringType):
            level = default_level
        else:
            level = path[1]
            path  = path[0]

        comps = self.splitPath(path)
        

        if level >=0:

            results = []
            for i in range(len(comps)):
                
                comp = comps[i]

                if not self._index.has_key(comp): return []
                if not self._index[comp].has_key(level+i): return []

                results.append( self._index[comp][level+i] )

            res = results[0]

            for i in range(1,len(results)):
                res = intersection(res,results[i])

            return res

        else:

            results = None

            for level in range(0,self._depth):
           
                ids = None
                error = 0

                for cn in range(0,len(comps)):
                    comp = comps[cn]

                    try: 
                        ids = intersection(ids,self._index[comp][level+cn])
                    except:
                        error = 1

                if error==0: 
                    results = union(results,ids)

            return results



    def __len__(self):
        """ len """
        return len(self._index)


    def numObjects(self):
        """ return the number of indexed objects"""

        x = IISet()
        for k,v in self._index.items():
            for level,ids in v.items():
                x = union(x,ids)

        return len(x)


    def keys(self):   
        """ return list of all path components """
        keys = []
        for k in self._index.keys(): keys.append(k)
        return keys


    def values(self):   
        values = []
        for k in self._index.values(): values.append(k)
        return values


    def items(self):   
        """ mapping path components : documentIds """

        items = []
        for k in self._index.items(): items.append(k)
        return items


    def _apply_index(self, request, cid=''): 
        """ hook for (Z)Catalog
        request   mapping type (usually {"path": "..." }
                  additionaly a parameter "path_level" might be passed
                  to specify the level (see search())

        cid      ???
        """

        record = parseIndexRequest(request,self.id,self.query_options)
        if record.keys==None: return None

        if request.has_key('%s_level' % cid):
            warnings.warn("The usage of the '%s_level' "
                          "is no longer recommended.\n"
                          "Please use a mapping object and the "
                          "'level' key to specify the operator." % cid)


        # get the level parameter 
        level    = record.get("level",0)

        # experimental code for specifing the operator
        operator = record.get('operator',self.useOperator).lower()

        # depending on the operator we use intersection of union
        if operator=="or":  set_func = union
        else:               set_func = intersection

        res = None

        for k in record.keys:
            rows = self.search(k,level)
            res = set_func(res,rows)

        if res:
            return res, (self.id,)
        else: 
            return IISet(), (self.id,)

    
    def uniqueValues(self,name=None,withLength=0):
        """ needed to be consistent with the interface """

        return self._index.keys()
        

    index_html = DTMLFile('dtml/index', globals())
    manage_workspace = DTMLFile('dtml/managePathIndex', globals())


manage_addPathIndexForm = DTMLFile('dtml/addPathIndex', globals())

def manage_addPathIndex(self, id, REQUEST=None, RESPONSE=None, URL3=None):
    """Add a path index"""
    return self.manage_addIndex(id, 'PathIndex', extra=None, \
                REQUEST=REQUEST, RESPONSE=RESPONSE, URL1=URL3)



