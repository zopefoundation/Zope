##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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

from Zope2.Startup import get_wsgi_starter
from Zope2.Startup.options import ZopeWSGIOptions

import io
import os
import shutil
import six
import sys
import tempfile
import unittest
import ZConfig


_SCHEMA = None


def getSchema():
    global _SCHEMA
    if _SCHEMA is None:
        opts = ZopeWSGIOptions()
        opts.load_schema()
        _SCHEMA = opts.schema
    return _SCHEMA


class WSGIStarterTestCase(unittest.TestCase):

    def setUp(self):
        self.TEMPNAME = tempfile.mktemp()

    def tearDown(self):
        shutil.rmtree(self.TEMPNAME)

    def get_starter(self, conf):
        starter = get_wsgi_starter()
        starter.setConfiguration(conf)
        return starter

    def load_config_text(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        text = text.replace("<<INSTANCE_HOME>>", self.TEMPNAME)
        if six.PY2:
            sio = io.BytesIO(text)
        else:
            sio = io.StringIO(text)

        try:
            os.mkdir(self.TEMPNAME)
        except OSError as why:
            if why == 17:
                # already exists
                pass
        conf, self.handler = ZConfig.loadConfigFile(getSchema(), sio)
        self.assertEqual(conf.instancehome, self.TEMPNAME)
        return conf

    def testSetupLocale(self):
        # XXX this almost certainly won't work on all systems
        import locale
        try:
            try:
                conf = self.load_config_text("""
                    instancehome <<INSTANCE_HOME>>
                    locale en_GB""")
            except ZConfig.DataConversionError as e:
                # Skip this test if we don't have support.
                if e.message.startswith(
                        'The specified locale "en_GB" is not supported'):
                    return
                raise
            starter = self.get_starter(conf)
            starter.setupLocale()
            self.assertEqual(tuple(locale.getlocale()), ('en_GB', 'ISO8859-1'))
        finally:
            # reset to system-defined locale
            locale.setlocale(locale.LC_ALL, '')

    def testSetupConflictRetries(self):
        from Zope2.Startup.handlers import root_wsgi_handler
        from ZPublisher.HTTPRequest import HTTPRequest

        # If no value is provided, the default is 3 retries
        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>""")
        root_wsgi_handler(conf)
        self.assertEqual(HTTPRequest.retry_max_count, 3)

        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>
            max-conflict-retries 25""")
        root_wsgi_handler(conf)
        self.assertEqual(HTTPRequest.retry_max_count, 25)

    @unittest.skipUnless(six.PY2, 'Python 2 specific checkinterval test.')
    def testConfigureInterpreter(self):
        oldcheckinterval = sys.getcheckinterval()
        newcheckinterval = oldcheckinterval + 1
        conf = self.load_config_text("""
                    instancehome <<INSTANCE_HOME>>
                    python-check-interval %d
                    """ % newcheckinterval)
        try:
            starter = self.get_starter(conf)
            starter.setupInterpreter()
            self.assertEqual(sys.getcheckinterval(), newcheckinterval)
        finally:
            sys.setcheckinterval(oldcheckinterval)
