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
    return ZODB.DB(s).open()


def createBigFile():
    # Create a file that is several 1<<16 blocks of data big, to force the
    # use of chained Pdata objects.
    # Make sure we create a file that isn't of x * 1<<16 length! Coll #671
    import io
    import random
    import string
    size = (1 << 16) * 5 + 12345
    file = io.BytesIO()

    for byte in range(size):
        letter = random.choice(string.ascii_letters)
        file.write(letter.encode('utf-8'))

    return file


TESTFOLDER_NAME = 'RangesTestSuite_testFolder'
BIGFILE = createBigFile()


class TestRequestRange(unittest.TestCase):

    # Test case setup and teardown
    def setUp(self):
        import io
        import string

        import transaction
        from OFS.Application import Application
        from OFS.Folder import manage_addFolder
        from OFS.Image import manage_addFile
        from Testing.makerequest import makerequest
        self.responseOut = io.BytesIO()
        self.connection = makeConnection()
        try:
            r = self.connection.root()
            a = Application()
            r['Application'] = a
            self.root = a
            self.app = makerequest(self.root, stdout=self.responseOut)
            try:
                self.app._delObject(TESTFOLDER_NAME)
            except AttributeError:
                pass
            manage_addFolder(self.app, TESTFOLDER_NAME)
            folder = getattr(self.app, TESTFOLDER_NAME)

            data = string.ascii_letters.encode('ascii')
            manage_addFile(
                folder, 'file', file=data, content_type='text/plain')

            self.file = folder.file
            self.data = data

            # Hack, we need a _p_mtime for the file, so we make sure that it
            # has one. We use a subtransaction, which means we can rollback
            # later and pretend we didn't touch the ZODB.
            transaction.commit()
        except Exception:
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
            body = body.split(b'\r\n\r\n', 1)[1]

        return body + rv

    def createLastModifiedDate(self, offset=0):
        from zope.datetime import rfc1123_date
        return rfc1123_date(self.file._p_mtime + offset)

    def expectUnsatisfiable(self, range):
        req = self.app.REQUEST
        rsp = req.RESPONSE

        # Add the Range header
        req.environ['HTTP_RANGE'] = 'bytes=%s' % range

        body = self.doGET(req, rsp)

        self.assertTrue(rsp.getStatus() == 416)

        expect_content_range = 'bytes */%d' % len(self.data)
        content_range = rsp.getHeader('content-range')
        self.assertFalse(content_range is None)
        self.assertEqual(content_range, expect_content_range)
        self.assertEqual(body, b'')

    def expectOK(self, rangeHeader, if_range=None):
        req = self.app.REQUEST
        rsp = req.RESPONSE

        # Add headers
        req.environ['HTTP_RANGE'] = rangeHeader
        if if_range is not None:
            req.environ['HTTP_IF_RANGE'] = if_range

        self.doGET(req, rsp)
        self.assertEqual(rsp.getStatus(), 200)

    def expectSingleRange(self, range, start, end, if_range=None):
        req = self.app.REQUEST
        rsp = req.RESPONSE

        # Add headers
        req.environ['HTTP_RANGE'] = 'bytes=%s' % range
        if if_range is not None:
            req.environ['HTTP_IF_RANGE'] = if_range

        body = self.doGET(req, rsp)
        self.assertEqual(rsp.getStatus(), 206)

        expect_content_range = 'bytes %d-%d/%d' % (
            start, end - 1, len(self.data))
        content_range = rsp.getHeader('content-range')
        self.assertFalse(content_range is None)
        self.assertEqual(content_range, expect_content_range)
        self.assertEqual(rsp.getHeader('content-length'), str(len(body)))
        self.assertEqual(body, self.data[start:end])

    def expectMultipleRanges(self, range, sets, draft=0):
        import email
        import io
        import re
        rangeParse = re.compile(r'bytes\s*(\d+)-(\d+)/(\d+)')
        req = self.app.REQUEST
        rsp = req.RESPONSE

        # Add headers
        req.environ['HTTP_RANGE'] = 'bytes=%s' % range

        if draft:
            req.environ['HTTP_REQUEST_RANGE'] = 'bytes=%s' % range

        body = self.doGET(req, rsp)

        self.assertTrue(rsp.getStatus() == 206)
        self.assertFalse(rsp.getHeader('content-range'))

        ct = rsp.getHeader('content-type').split(';')[0]
        draftprefix = draft and 'x-' or ''
        self.assertEqual(ct, 'multipart/%sbyteranges' % draftprefix)
        if rsp.getHeader('content-length'):
            self.assertEqual(rsp.getHeader('content-length'), str(len(body)))

        # Decode the multipart message and force a latin-1 encoding,
        # revert that later after the email was parsed
        bodyfile = io.StringIO(
            'Content-Type: '
            + rsp.getHeader('content-type')
            + '\n\n' + body.decode('latin-1')
        )

        # This needs text, hence the forced latin-1 decoding.
        msg = email.message_from_file(bodyfile)
        partmessages = [part for part in msg.walk()]

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

            self.assertEqual(size, len(self.data))
            # revert earlier fake latin-1 encoding
            body = part.get_payload().encode('latin-1')

            self.assertEqual(len(body), end - start)
            self.assertEqual(body, self.data[start:end])

            add((start, end))

        # Compare the ranges used with the expected range sets.
        self.assertEqual(returnedRanges, sets)

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
        length = len(self.data)
        self.expectSingleRange('-3', length - 3, length)

    def testWithNegativeZero(self):
        # A satisfiable and an unsatisfiable range
        self.expectSingleRange('-0,3-23', 3, 24)

    def testEndOverflow(self):
        length = len(self.data)
        start, end = length - 10, length + 10
        range = '%d-%d' % (start, end)
        self.expectSingleRange(range, start, len(self.data))

    def testBigFile(self):
        # Files of size 1<<16 are stored in linked Pdata objects. They are
        # treated seperately in the range code.
        self.uploadBigFile()
        join = 3 * (1 << 16)  # A join between two linked objects
        start = join - 1000
        end = join + 1000
        range = '%d-%d' % (start, end - 1)
        self.expectSingleRange(range, start, end)

    def testBigFileEndOverflow(self):
        self.uploadBigFile()
        length = len(self.data)
        start, end = length - 100, length + 100
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
        self.expectMultipleRanges(
            '3-700,10-15,-10000',
            [(3, 701), (10, 16), (len(self.data) - 10000, len(self.data))])

    def testMultipleRangesBigFileOutOfOrder(self):
        self.uploadBigFile()
        self.expectMultipleRanges(
            '10-15,-10000,70000-80000',
            [(10, 16), (len(self.data) - 10000, len(self.data)),
             (70000, 80001)])

    def testMultipleRangesBigFileEndOverflow(self):
        self.uploadBigFile()
        length = len(self.data)
        start, end = length - 100, length + 100
        self.expectMultipleRanges(
            f'3-700,{start}-{end}',
            [(3, 701), (len(self.data) - 100, len(self.data))])

    # If-Range headers
    def testIllegalIfRange(self):
        # We assume that an illegal if-range is to be ignored, just like an
        # illegal if-modified since.
        self.expectSingleRange('10-25', 10, 26, if_range='garbage')

    def testEqualIfRangeDate(self):
        self.expectSingleRange(
            '10-25', 10, 26,
            if_range=self.createLastModifiedDate()
        )

    def testIsModifiedIfRangeDate(self):
        self.expectOK(
            '21-25,10-20',
            if_range=self.createLastModifiedDate(offset=-100)
        )

    def testIsNotModifiedIfRangeDate(self):
        self.expectSingleRange(
            '10-25', 10, 26,
            if_range=self.createLastModifiedDate(offset=100)
        )

    def testEqualIfRangeEtag(self):
        self.expectSingleRange(
            '10-25', 10, 26,
            if_range=self.file.http__etag()
        )

    def testNotEqualIfRangeEtag(self):
        self.expectOK(
            '10-25',
            if_range=self.file.http__etag() + 'bar'
        )
