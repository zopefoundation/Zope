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

import os, sys
execfile(os.path.join(sys.path[0], 'framework.py'))

from PathIndex.PathIndex import PathIndex


class Dummy:

    meta_type="foo"
    def __init__( self, path):
        self.path = path

    def getPhysicalPath(self):
        return self.path.split('/')

    
    def __str__( self ):
        return '<Dummy: %s>' % self.path
    
    __repr__ = __str__

class TestCase( unittest.TestCase ):
    """
        Test PathIndex objects.
    """

    def setUp( self ):
        """
        """
        self._index = PathIndex( 'path' )
        self._values = {
          1 : Dummy("/aa/aa/aa/1.html"),
          2 : Dummy("/aa/aa/bb/2.html"),
          3 : Dummy("/aa/aa/cc/3.html"),
          4 : Dummy("/aa/bb/aa/4.html"),
          5 : Dummy("/aa/bb/bb/5.html"),
          6 : Dummy("/aa/bb/cc/6.html"),
          7 : Dummy("/aa/cc/aa/7.html"),
          8 : Dummy("/aa/cc/bb/8.html"),
          9 : Dummy("/aa/cc/cc/9.html"),
          10 : Dummy("/bb/aa/aa/10.html"),
          11 : Dummy("/bb/aa/bb/11.html"),
          12 : Dummy("/bb/aa/cc/12.html"),
          13 : Dummy("/bb/bb/aa/13.html"),
          14 : Dummy("/bb/bb/bb/14.html"),
          15 : Dummy("/bb/bb/cc/15.html"),
          16 : Dummy("/bb/cc/aa/16.html"),
          17 : Dummy("/bb/cc/bb/17html"),
          18 : Dummy("/bb/cc/cc/18html")
        }


    def tearDown( self ):
        """
        """

    def _populateIndex( self ):
        for k, v in self._values.items():
            self._index.index_object( k, v )

           
    def testEmpty( self ):
        "Test an empty PathIndex."

        assert len( self._index ) == 0
        assert self._index.getEntryForObject( 1234 ) is None
        self._index.unindex_object( 1234 ) # nothrow
        assert self._index._apply_index( {"suxpath":"xxx"} ) is None


    def testUnIndex( self ):
        "Test to UnIndex PathIndex."

        self._populateIndex()

        for k in self._values.keys():
            self._index.unindex_object(k)

        assert len(self._index._index)==0
        assert len(self._index._unindex)==0

    
    def testPopulateIndex( self ):

        self._populateIndex()
        
        tests = [
            ("aa",0, [1,2,3,4,5,6,7,8,9]),
            ("aa",1, [1,2,3,10,11,12] ),
            ("bb",0, [10,11,12,13,14,15,16,17,18]),
            ("bb",1, [4,5,6,13,14,15] ),
            ("bb/cc",0, [16,17,18] ),
            ("bb/cc",1, [6,15] ),
            ("bb/aa",0, [10,11,12] ),
            ("bb/aa",1, [4,13] ),
            ("aa/cc",-1, [3,7,8,9,12] ),
            ("bb/bb",-1, [5,13,14,15] )
        ]

        for comp,level,results in tests:
            for path in [comp,"/"+comp,"/"+comp+"/"]:
                res = self._index._apply_index({"path":{'query':path,"level":level}})
                lst = list(res[0].keys())
                assert lst==results,res

        for comp,level,results in tests:
            for path in [comp,"/"+comp,"/"+comp+"/"]:
                res = self._index._apply_index({"path":{'query':( (path,level),)}})
                lst = list(res[0].keys())
                assert lst==results,res
    
framework()
