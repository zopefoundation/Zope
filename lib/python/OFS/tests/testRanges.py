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
import os, sys, unittest

import string, whrandom, cStringIO, time, re
import ZODB
from OFS.Application import Application
from OFS.Folder import manage_addFolder
from OFS.Image import manage_addFile
from Testing.makerequest import makerequest
from webdav.common import rfc1123_date

from mimetools import Message
from multifile import MultiFile

def makeConnection():
    import ZODB
    from ZODB.DemoStorage import DemoStorage

    dfi = os.path.join( os.environ['SOFTWARE_HOME']
                      , '..', '..', 'var', 'Data.fs.in')
    dfi = os.path.abspath(dfi)
    s = DemoStorage(quota=(1<<20))
    return ZODB.DB( s ).open()

def createBigFile():
    # Create a file that is several 1<<16 blocks of data big, to force the
    # use of chained Pdata objects.
    size = (1<<16) * 5
    file = cStringIO.StringIO()

    def addLetter(x, add=file.write, l=string.letters, 
            c=whrandom.choice):
        add(c(l))
    filter(addLetter, range(size))

    return file

TESTFOLDER_NAME = 'RangesTestSuite_testFolder'
BIGFILE = createBigFile()

class TestRequestRange(unittest.TestCase):
    # Test case setup and teardown
    def setUp(self):
        self.responseOut = cStringIO.StringIO()
        self.connection = makeConnection()
        try:
            r = self.connection.root()
            a = Application()
            r['Application'] = a
            self.root = a
            self.app = makerequest(self.root, stdout=self.responseOut)
            try: self.app._delObject(TESTFOLDER_NAME)
            except AttributeError: pass
            manage_addFolder(self.app, TESTFOLDER_NAME)
            folder = getattr( self.app, TESTFOLDER_NAME )

            data = string.letters
            manage_addFile( folder, 'file'
                          , file=data, content_type='text/plain')

            self.file = folder.file
            self.data = data

            # Hack, we need a _p_mtime for the file, so we make sure that it
            # has one. We use a subtransaction, which means we can rollback
            # later and pretend we didn't touch the ZODB.
            get_transaction().commit()
        except:
            self.connection.close()
            raise

    def tearDown(self):
        try: self.app._delObject(TESTFOLDER_NAME)
        except AttributeError: pass
        get_transaction().commit()
        self.connection.close()
        self.app = None
        del self.app

    # Utility methods
    def uploadBigFile(self):
        self.file.manage_upload(BIGFILE)
        self.data = BIGFILE.getvalue()

    def doGET(self, request, response):
        rv = self.file.index_html(request, response)

        # Large files are written to resposeOut directly, small ones are
        # returned from the index_html method.
        body = self.responseOut.getvalue()

        # Chop off any printed headers (only when response.write was used)
        if body:
            body = string.split(body, '\n\n', 1)[1]

        return body + rv

    def createLastModifiedDate(self, offset=0):
        return rfc1123_date(self.file._p_mtime + offset)
    
    def expectUnsatisfiable(self, range):
        req = self.app.REQUEST
        rsp = req.RESPONSE

        # Add the Range header
        req.environ['HTTP_RANGE'] = 'bytes=%s' % range

        body = self.doGET(req, rsp)
        
        self.failUnless(rsp.getStatus() == 416,
            'Expected a 416 status, got %s' % rsp.getStatus())

        expect_content_range = 'bytes */%d' % len(self.data)
        content_range = rsp.getHeader('content-range')
        self.failIf(content_range is None, 'No Content-Range header was set!')
        self.failUnless(content_range == expect_content_range,
            'Received incorrect Content-Range header. Expected %s, got %s' % (
                `expect_content_range`, `content_range`))

        self.failUnless(body == '', 'index_html returned %s' % `body`)

    def expectOK(self, rangeHeader, if_range=None):
        req = self.app.REQUEST
        rsp = req.RESPONSE

        # Add headers
        req.environ['HTTP_RANGE'] = rangeHeader
        if if_range is not None:
            req.environ['HTTP_IF_RANGE'] = if_range

        body = self.doGET(req, rsp)
        
        self.failUnless(rsp.getStatus() == 200,
            'Expected a 200 status, got %s' % rsp.getStatus())

    def expectSingleRange(self, range, start, end, if_range=None):
        req = self.app.REQUEST
        rsp = req.RESPONSE

        # Add headers
        req.environ['HTTP_RANGE'] = 'bytes=%s' % range
        if if_range is not None:
            req.environ['HTTP_IF_RANGE'] = if_range

        body = self.doGET(req, rsp)
        
        self.failUnless(rsp.getStatus() == 206,
            'Expected a 206 status, got %s' % rsp.getStatus())

        expect_content_range = 'bytes %d-%d/%d' % (
            start, end - 1, len(self.data))
        content_range = rsp.getHeader('content-range')
        self.failIf(content_range is None, 'No Content-Range header was set!')
        self.failUnless(content_range == expect_content_range,
            'Received incorrect Content-Range header. Expected %s, got %s' % (
                `expect_content_range`, `content_range`))
        self.failIf(rsp.getHeader('content-length') != len(body),
            'Incorrect Content-Length is set! Expected %d, got %d.' % (
                rsp.getHeader('content-length'), len(body)))

        self.failUnless(body == self.data[start:end], 
            'Incorrect range returned, expected %s, got %s' % (
                `self.data[start:end]`, `body`))

    def expectMultipleRanges(self, range, sets, 
            rangeParse=re.compile('bytes\s*(\d+)-(\d+)/(\d+)')):
        req = self.app.REQUEST
        rsp = req.RESPONSE

        # Add headers
        req.environ['HTTP_RANGE'] = 'bytes=%s' % range

        body = self.doGET(req, rsp)
        
        self.failUnless(rsp.getStatus() == 206,
            'Expected a 206 status, got %s' % rsp.getStatus())
        self.failIf(rsp.getHeader('content-range'), 
            'The Content-Range header should not be set!')

        ct = string.split(rsp.getHeader('content-type'), ';')[0]
        self.failIf(ct != 'multipart/byteranges',
            "Incorrect Content-Type set. Expected 'multipart/byteranges', "
            "got %s" % ct)
        if rsp.getHeader('content-length'):
            self.failIf(rsp.getHeader('content-length') != len(body),
                'Incorrect Content-Length is set! Expected %d, got %d.' % (
                    len(body), rsp.getHeader('content-length')))

        # Decode the multipart message
        bodyfile = cStringIO.StringIO('Content-Type: %s\n\n%s' % (
            rsp.getHeader('content-type'), body))
        bodymessage = Message(bodyfile)
        partfiles = MultiFile(bodyfile)
        partfiles.push(bodymessage.getparam('boundary'))

        partmessages = []
        add = partmessages.append
        while partfiles.next():
            add(Message(cStringIO.StringIO(partfiles.read())))

        # Check the different parts
        returnedRanges = []
        add = returnedRanges.append
        for part in partmessages:
            range = part['content-range']
            start, end, size = rangeParse.search(range).groups()
            start, end, size = int(start), int(end), int(size)
            end = end + 1

            self.failIf(size != len(self.data),
                'Part Content-Range header reported incorrect length. '
                'Expected %d, got %d.' % (len(self.data), size))

            part.rewindbody()
            body = part.fp.read()
            # Whotcha! Bug in MultiFile; the CRLF that is part of the boundary
            # is returned as part of the body. Note that this bug is resolved
            # in Python 2.2.
            if body[-2:] == '\r\n':
                body = body[:-2]
            
            self.failIf(len(body) != end - start,
                'Part (%d, %d) is of wrong length, expected %d, got %d.' % (
                    start, end, end - start, len(body)))
            self.failIf(body != self.data[start:end],
                'Part (%d, %d) has incorrect data. Expected %s, got %s.' % (
                    start, end, `self.data[start:end]`, `body`))

            add((start, end))

        # Copmare the ranges used with the expected range sets.
        self.failIf(returnedRanges != sets,
            'Got unexpected sets, expected %s, got %s' % (
                sets, returnedRanges))

    # Unsatisfiable requests
    def testNegativeZero(self):
        self.expectUnsatisfiable('-0')

    def testStartBeyondLength(self):
        self.expectUnsatisfiable('1000-')

    def testMultipleUnsatisfiable(self):
        self.expectUnsatisfiable('1000-1001,2000-,-0')

    # Malformed Range header
    def testGarbage(self):
        self.expectOK('kjhdkjhd = ew;jkj h eewh ew')

    def testIllegalSpec(self):
        self.expectOK('notbytes=0-1000')

    # Single ranges
    def testSimpleRange(self):
        self.expectSingleRange('3-7', 3, 8)

    def testOpenEndedRange(self):
        self.expectSingleRange('3-', 3, len(self.data))

    def testSuffixRange(self):
        l = len(self.data)
        self.expectSingleRange('-3', l - 3, l)

    def testWithNegativeZero(self):
        # A satisfiable and an unsatisfiable range
        self.expectSingleRange('-0,3-23', 3, 24)

    def testAdjacentRanges(self):
        self.expectSingleRange('21-25,10-20', 10, 26)

    def testEndOverflow(self):
        l = len(self.data)
        start, end = l - 10, l + 10
        range = '%d-%d' % (start, end)
        self.expectSingleRange(range, start, len(self.data))

    def testBigFile(self):
        # Files of size 1<<16 are stored in linked Pdata objects. They are
        # treated seperately in the range code.
        self.uploadBigFile()
        join = 3 * (1<<16) # A join between two linked objects
        start = join - 1000
        end = join + 1000
        range = '%d-%d' % (start, end - 1)
        self.expectSingleRange(range, start, end)

    def testBigFileEndOverflow(self):
        self.uploadBigFile()
        l = len(self.data)
        start, end = l - 100, l + 100
        range = '%d-%d' % (start, end)
        self.expectSingleRange(range, start, len(self.data))

    # Multiple ranges
    def testMultipleRanges(self):
        self.expectMultipleRanges('3-7,10-15', [(3, 8), (10, 16)])

    def testMultipleRangesBigFile(self):
        self.uploadBigFile()
        self.expectMultipleRanges('3-700,10-15,-10000', 
            [(3, 701), (len(self.data) - 10000, len(self.data))])

    def testMultipleRangesBigFileEndOverflow(self):
        self.uploadBigFile()
        l = len(self.data)
        start, end = l - 100, l + 100
        self.expectMultipleRanges('3-700,%s-%s' % (start, end), 
            [(3, 701), (len(self.data) - 100, len(self.data))])

    # If-Range headers
    def testIllegalIfRange(self):
        # We assume that an illegal if-range is to be ignored, just like an
        # illegal if-modified since.
        self.expectSingleRange('21-25,10-20', 10, 26, if_range='garbage')

    def testEqualIfRangeDate(self):
        self.expectSingleRange('21-25,10-20', 10, 26,
            if_range=self.createLastModifiedDate())

    def testIsModifiedIfRangeDate(self):
        self.expectOK('21-25,10-20',
            if_range=self.createLastModifiedDate(offset=-100))

    def testIsNotModifiedIfRangeDate(self):
        self.expectSingleRange('21-25,10-20', 10, 26,
            if_range=self.createLastModifiedDate(offset=100))

    def testEqualIfRangeEtag(self):
        self.expectSingleRange('21-25,10-20', 10, 26,
            if_range=self.file.http__etag())

    def testNotEqualIfRangeEtag(self):
        self.expectOK('21-25,10-20',
            if_range=self.file.http__etag() + 'bar')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestRequestRange ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
