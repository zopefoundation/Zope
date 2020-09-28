##############################################################################
#
# Copyright (c) 2017 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import unittest

from ZPublisher.http_header_utils import make_content_disposition


class MakeDispositionHeaderTests(unittest.TestCase):

    def test_ascii(self):
        self.assertEqual(
            make_content_disposition("inline", "iq.png"),
            'inline; filename="iq.png"')

    def test_unicode(self):
        """HTTP headers need to be latin-1 compatible

        In order to offer file downloads which contain unicode file names,
        the file name has to be treated in a special way, see
        https://stackoverflow.com/questions/1361604 .
        """
        self.assertEqual(
            make_content_disposition("inline", "ıq.png"),
            """inline; filename="q.png"; filename*=UTF-8''%C4%B1q.png"""
        )
