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
import sys, os, time, whrandom, unittest

if __name__ == "__main__":
    sys.path.insert(0, '../../..')
    #os.chdir('../../..')

import ZODB
from Products.Transience.Transience import \
     TransientObjectContainer, TransientObject
import Products.Transience.Transience
from unittest import TestCase, TestSuite, TextTestRunner, makeSuite

epoch = time.time()

class TestTransientObject(TestCase):
    def setUp(self):
        self.errmargin = .20
        self.timeout = 60
        Products.Transience.Transience.time = fauxtime
        self.t = TransientObjectContainer('sdc', timeout_mins=self.timeout/60)

    def tearDown(self):
        self.t = None
        del self.t
        
    def test_id(self):
        t = self.t.new('xyzzy')
        assert t.getId() != 'xyzzy'

    def test_validate(self):
        t = self.t.new('xyzzy')
        assert t.isValid()
        t.invalidate()
        assert not t.isValid()

    def test_getLastAccessed(self):
        t = self.t.new('xyzzy')
        ft = fauxtime()
        assert t.getLastAccessed() <= ft

    def test_getCreated(self):
        t = self.t.new('xyzzy')
        ft = fauxtime()
        assert t.getCreated() <= ft

    def test_setLastAccessed(self):
        t = self.t.new('xyzzy')
        ft = fauxtime()
        assert t.getLastAccessed() <= ft
        fauxsleep(self.timeout)   # go to sleep past the granuarity
        ft2 = fauxtime()
        t.setLastAccessed()
        ft3 = fauxtime()
        assert t.getLastAccessed() <= ft3
        assert t.getLastAccessed() >= ft2

    def _genKeyError(self, t):
        return t.get('foobie')

    def _genLenError(self, t):
        return t.len()

    def test_dictionaryLike(self):
        t = self.t.new('keytest')
        t.update(data)
        assert t.keys() == data.keys()
        assert t.values() == data.values()
        assert t.items() == data.items()
        for k in data.keys():
            assert t.get(k) == data.get(k)
        self.assertRaises(KeyError, self._genKeyError, t)
        self.assertRaises(AttributeError, self._genLenError, t)
        assert t.get('foobie',None) is None
        assert t.has_key('a') 
        assert not t.has_key('foobie') 
        t.clear()
        assert not len(t.keys()) 

    def test_TTWDictionary(self):
        t = self.t.new('mouthfultest')
        t.set('foo', 'bar')
        assert t['foo'] == 'bar'
        assert t.get('foo') == 'bar'
        t.set('foobie', 'blech')
        t.delete('foobie')
        self.assertRaises(KeyError, self._genKeyError, t)


def test_suite():
    testsuite = makeSuite(TestTransientObject, 'test')
    alltests = TestSuite((testsuite,))
    return alltests

def fauxtime():
    """ False timer -- returns time 10 x faster than normal time """
    return (time.time() - epoch) * 10.0

def fauxsleep(duration):
    """ False sleep -- sleep for 1/10 the time specifed """
    time.sleep(duration / 10.0)

data = {
    'a': 'a',
    1: 1,
    'Mary': 'no little lamb for you today!',
    'epoch': epoch,
    'fauxtime': fauxtime
    }

if __name__ == '__main__':
    runner = TextTestRunner(verbosity=9)
    runner.run(test_suite())

