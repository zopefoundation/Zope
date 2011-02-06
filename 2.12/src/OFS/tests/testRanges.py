##############################################################################
#
# Copyright (c) 2002-2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import unittest

def makeConnection():
    import ZODB
    from ZODB.DemoStorage import DemoStorage

    s = DemoStorage()
    return ZODB.DB( s ).open()

def createBigFile():
    # Create a file that is several 1<<16 blocks of data big, to force the
    # use of chained Pdata objects.
    # Make sure we create a file that isn't of x * 1<<16 length! Coll #671
    import cStringIO
    import random
    import string
    size = (1<<16) * 5 + 12345
    file = cStringIO.StringIO()

    def addLetter(x, add=file.write, l=string.letters,
            c=random.choice):
        add(c(l))
    filter(addLetter, range(size))

    return file

TESTFOLDER_NAME = 'RangesTestSuite_testFolder'
BIGFILE = createBigFile()

class TestRequestRange(unittest.TestCase):
    # Test case setup and teardown
    def setUp(self):
        import cStringIO
        import string
        import transaction
        from OFS.Application import Application
        from OFS.Folder import manage_addFolder
        from OFS.Image import manage_addFile
        from Testing.makerequest import makerequest
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
            transaction.commit()
        except:
            self.connection.close()
            raise

    def tearDown(self):
        import transaction
        try:
            self.app._delObject(TESTFOLDER_NAME)
        except AttributeError:
            pass
        transaction.abort()
        self.app._p_jar.sync()
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
            body = body.split('\r\n\r\n', 1)[1]

        return body + rv

    def createLastModifiedDate(self, offset=0):
        from webdav.common import rfc1123_date
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
        self.failIf(rsp.getHeader('content-length') != str(len(body)),
            'Incorrect Content-Length is set! Expected %s, got %s.' % (
                str(len(body)), rsp.getHeader('content-length')))

        self.failUnless(body == self.data[start:end],
            'Incorrect range returned, expected %s, got %s' % (
                `self.data[start:end]`, `body`))

    def expectMultipleRanges(self, range, sets, draft=0):
        import cStringIO
        import re
        import email
        rangeParse = re.compile('bytes\s*(\d+)-(\d+)/(\d+)')
        req = self.app.REQUEST
        rsp = req.RESPONSE

        # Add headers
        req.environ['HTTP_RANGE'] = 'bytes=%s' % range

        if draft:
            req.environ['HTTP_REQUEST_RANGE'] = 'bytes=%s' % range

        body = self.doGET(req, rsp)

        self.failUnless(rsp.getStatus() == 206,
            'Expected a 206 status, got %s' % rsp.getStatus())
        self.failIf(rsp.getHeader('content-range'),
            'The Content-Range header should not be set!')

        ct = rsp.getHeader('content-type').split(';')[0]
        draftprefix = draft and 'x-' or ''
        self.failIf(ct != 'multipart/%sbyteranges' % draftprefix,
            "Incorrect Content-Type set. Expected 'multipart/%sbyteranges', "
            "got %s" % (draftprefix, ct))
        if rsp.getHeader('content-length'):
            self.failIf(rsp.getHeader('content-length') != str(len(body)),
                'Incorrect Content-Length is set! Expected %s, got %s.' % (
                    str(len(body)), rsp.getHeader('content-length')))

        # Decode the multipart message
        bodyfile = cStringIO.StringIO('Content-Type: %s\n\n%s' % (
            rsp.getHeader('content-type'), body))
        partmessages = [part
                        for part in email.message_from_file(bodyfile).walk()]

        # Check the different parts
        returnedRanges = []
        add = returnedRanges.append
        for part in partmessages:
            if part.get_content_maintype() == 'multipart':
                continue
            range = part.get('content-range')
            start, end, size = rangeParse.search(range).groups()
            start, end, size = int(start), int(end), int(size)
            end = end + 1

            self.failIf(size != len(self.data),
                'Part Content-Range header reported incorrect length. '
                'Expected %d, got %d.' % (len(self.data), size))

            body = part.get_payload()

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
    def testAdjacentRanges(self):
        self.expectMultipleRanges('21-25,10-20', [(21, 26), (10, 21)])

    def testMultipleRanges(self):
        self.expectMultipleRanges('3-7,10-15', [(3, 8), (10, 16)])

    def testMultipleRangesDraft(self):
        self.expectMultipleRanges('3-7,10-15', [(3, 8), (10, 16)], draft=1)

    def testMultipleRangesBigFile(self):
        self.uploadBigFile()
        self.expectMultipleRanges('3-700,10-15,-10000',
            [(3, 701), (10, 16), (len(self.data) - 10000, len(self.data))])

    def testMultipleRangesBigFileOutOfOrder(self):
        self.uploadBigFile()
        self.expectMultipleRanges('10-15,-10000,70000-80000', 
            [(10, 16), (len(self.data) - 10000, len(self.data)),
             (70000, 80001)])

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
        self.expectSingleRange('10-25', 10, 26, if_range='garbage')

    def testEqualIfRangeDate(self):
        self.expectSingleRange('10-25', 10, 26,
            if_range=self.createLastModifiedDate())

    def testIsModifiedIfRangeDate(self):
        self.expectOK('21-25,10-20',
            if_range=self.createLastModifiedDate(offset=-100))

    def testIsNotModifiedIfRangeDate(self):
        self.expectSingleRange('10-25', 10, 26,
            if_range=self.createLastModifiedDate(offset=100))

    def testEqualIfRangeEtag(self):
        self.expectSingleRange('10-25', 10, 26,
            if_range=self.file.http__etag())

    def testNotEqualIfRangeEtag(self):
        self.expectOK('10-25',
            if_range=self.file.http__etag() + 'bar')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestRequestRange ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
