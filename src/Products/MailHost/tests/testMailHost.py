##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""MailHost unit tests.

$Id$
"""

import unittest
from email import message_from_string

from Products.MailHost.MailHost import MailHost
from Products.MailHost.MailHost import MailHostError, _mungeHeaders


class DummyMailHost(MailHost):
    meta_type = 'Dummy Mail Host'
    def __init__(self, id):
        self.id = id
        self.sent = ''
    def _send(self, mfrom, mto, messageText, immediate=False):
        self.sent = messageText
        self.immediate = immediate

class FakeContent(object):
    def __init__(self, template_name, message):
        def template(self, context, REQUEST=None):
            return message
        setattr(self, template_name, template)

    @staticmethod
    def check_status(context, REQUEST=None):
        return 'Message Sent'

class TestMailHost(unittest.TestCase):

    def _getTargetClass(self):
        return DummyMailHost

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_z3interfaces(self):
        from Products.MailHost.interfaces import IMailHost
        from zope.interface.verify import verifyClass

        verifyClass(IMailHost, self._getTargetClass())

    def testAllHeaders( self ):
        msg = """To: recipient@domain.com
From: sender@domain.com
Subject: This is the subject

This is the message body."""
        # No additional info
        resmsg, resto, resfrom = _mungeHeaders( msg )
        self.failUnless(resto == ['recipient@domain.com'])
        self.failUnless(resfrom == 'sender@domain.com' )

        # Add duplicated info
        resmsg, resto, resfrom = _mungeHeaders(msg, 'recipient@domain.com',
                                  'sender@domain.com', 'This is the subject' )
        self.failUnlessEqual(resto, ['recipient@domain.com'])
        self.failUnlessEqual(resfrom, 'sender@domain.com' )

        # Add extra info
        resmsg, resto, resfrom = _mungeHeaders(msg, 'recipient2@domain.com',
                            'sender2@domain.com', 'This is the real subject' )
        self.failUnlessEqual(resto, ['recipient2@domain.com'])
        self.failUnlessEqual(resfrom, 'sender2@domain.com' )

    def testMissingHeaders( self ):
        msg = """X-Header: Dummy header

This is the message body."""
        # Doesn't specify to
        self.failUnlessRaises(MailHostError, _mungeHeaders, msg,
                              mfrom='sender@domain.com')
        # Doesn't specify from
        self.failUnlessRaises(MailHostError, _mungeHeaders, msg,
                              mto='recipient@domain.com')

    def testNoHeaders( self ):
        msg = """This is the message body."""
        # Doesn't specify to
        self.failUnlessRaises(MailHostError, _mungeHeaders, msg,
                              mfrom='sender@domain.com')
        # Doesn't specify from
        self.failUnlessRaises(MailHostError, _mungeHeaders, msg,
                              mto='recipient@domain.com')
        # Specify all
        resmsg, resto, resfrom = _mungeHeaders(msg, 'recipient2@domain.com',
                             'sender2@domain.com', 'This is the real subject')
        self.failUnlessEqual(resto, ['recipient2@domain.com'])
        self.failUnlessEqual(resfrom,'sender2@domain.com' )

    def testBCCHeader( self ):
        msg = "From: me@example.com\nBcc: many@example.com\n\nMessage text"
        # Specify only the "Bcc" header.  Useful for bulk emails.
        resmsg, resto, resfrom = _mungeHeaders(msg)
        self.failUnlessEqual(resto, ['many@example.com'])
        self.failUnlessEqual(resfrom, 'me@example.com' )


    def testAddressParser( self ):
        msg = """To: "Name, Nick" <recipient@domain.com>, "Foo Bar" <foo@domain.com>
CC: "Web, Jack" <jack@web.com>
From: sender@domain.com
Subject: This is the subject

This is the message body."""
        
        # Test Address-Parser for To & CC given in messageText
        
        resmsg, resto, resfrom = _mungeHeaders( msg )
        self.failUnlessEqual(resto, ['"Name, Nick" <recipient@domain.com>',
                                  'Foo Bar <foo@domain.com>',
                                  '"Web, Jack" <jack@web.com>'])
        self.failUnlessEqual(resfrom, 'sender@domain.com')

        # Test Address-Parser for a given mto-string
        
        resmsg, resto, resfrom = _mungeHeaders(msg, mto= '"Public, Joe" <pjoe@domain.com>, Foo Bar <foo@domain.com>')

        self.failUnlessEqual(resto, ['"Public, Joe" <pjoe@domain.com>',
                                  'Foo Bar <foo@domain.com>'])
        self.failUnlessEqual(resfrom, 'sender@domain.com')

    def testSendMessageOnly(self):
        msg = """\
To: "Name, Nick" <recipient@domain.com>, "Foo Bar" <foo@domain.com>
From: sender@domain.com
Subject: This is the subject
Date: Sun, 27 Aug 2006 17:00:00 +0200

This is the message body."""

        mailhost = self._makeOne('MailHost')
        mailhost.send(msg)
        self.assertEqual(mailhost.sent, msg)

    def testSendWithArguments(self):
        inmsg = """\
Date: Sun, 27 Aug 2006 17:00:00 +0200

This is the message body."""

        outmsg = """\
Date: Sun, 27 Aug 2006 17:00:00 +0200
Subject: This is the subject
To: "Name, Nick" <recipient@domain.com>, Foo Bar <foo@domain.com>
From: sender@domain.com

This is the message body."""

        mailhost = self._makeOne('MailHost')
        mailhost.send(messageText=inmsg,
                      mto='"Name, Nick" <recipient@domain.com>, "Foo Bar" <foo@domain.com>',
                      mfrom='sender@domain.com', subject='This is the subject')
        self.assertEqual(mailhost.sent, outmsg)

    def testSendWithMtoList(self):
        inmsg = """\
Date: Sun, 27 Aug 2006 17:00:00 +0200

This is the message body."""

        outmsg = """\
Date: Sun, 27 Aug 2006 17:00:00 +0200
Subject: This is the subject
To: "Name, Nick" <recipient@domain.com>, Foo Bar <foo@domain.com>
From: sender@domain.com

This is the message body."""

        mailhost = self._makeOne('MailHost')
        mailhost.send(messageText=inmsg,
                      mto=['"Name, Nick" <recipient@domain.com>', '"Foo Bar" <foo@domain.com>'],
                      mfrom='sender@domain.com', subject='This is the subject')
        self.assertEqual(mailhost.sent, outmsg)

    def testSimpleSend(self):
        outmsg = """\
From: sender@domain.com
To: "Name, Nick" <recipient@domain.com>, "Foo Bar" <foo@domain.com>
Subject: This is the subject

This is the message body."""

        mailhost = self._makeOne('MailHost')
        mailhost.simple_send(mto='"Name, Nick" <recipient@domain.com>, "Foo Bar" <foo@domain.com>',
                             mfrom='sender@domain.com', subject='This is the subject',
                             body='This is the message body.')
        self.assertEqual(mailhost.sent, outmsg)
        self.assertEqual(mailhost.immediate, False)

    def testSendImmediate(self):
        outmsg = """\
From: sender@domain.com
To: "Name, Nick" <recipient@domain.com>, "Foo Bar" <foo@domain.com>
Subject: This is the subject

This is the message body."""

        mailhost = self._makeOne('MailHost')
        mailhost.simple_send(mto='"Name, Nick" <recipient@domain.com>, "Foo Bar" <foo@domain.com>',
                             mfrom='sender@domain.com', subject='This is the subject',
                             body='This is the message body.', immediate=True)
        self.assertEqual(mailhost.sent, outmsg)
        self.assertEqual(mailhost.immediate, True)

    def testSendBodyWithUrl(self):
        # The implementation of rfc822.Message reacts poorly to
        # message bodies containing ':' characters as in a url
        msg = "Here's a nice link: http://www.zope.org/"

        mailhost = self._makeOne('MailHost')
        mailhost.send(messageText=msg,
                      mto='"Name, Nick" <recipient@domain.com>, "Foo Bar" <foo@domain.com>',
                      mfrom='sender@domain.com', subject='This is the subject')
        out = message_from_string(mailhost.sent)
        self.failUnlessEqual(out.get_payload(), msg)
        self.failUnlessEqual(out['To'],
                             '"Name, Nick" <recipient@domain.com>, Foo Bar <foo@domain.com>')
        self.failUnlessEqual(out['From'], 'sender@domain.com')

    def testSendEncodedBody(self):
        # If a charset is specified the correct headers for content
        # encoding will be set if not already set.  Additionally, if
        # there is a default transfer encoding for the charset, then
        # the content will be encoded and the transfer encoding header
        # will be set.
        msg = "Here's some encoded t\xc3\xa9xt."
        mailhost = self._makeOne('MailHost')
        mailhost.send(messageText=msg,
                      mto='"Name, Nick" <recipient@domain.com>, "Foo Bar" <foo@domain.com>',
                      mfrom='sender@domain.com', subject='This is the subject', charset='utf-8')
        out = message_from_string(mailhost.sent)
        self.failUnlessEqual(out['To'],
                             '"Name, Nick" <recipient@domain.com>, Foo Bar <foo@domain.com>')
        self.failUnlessEqual(out['From'], 'sender@domain.com')
        # utf-8 will default to Quoted Printable encoding
        self.failUnlessEqual(out['Content-Transfer-Encoding'],
                             'quoted-printable')
        self.failUnlessEqual(out['Content-Type'], 'text/plain; charset="utf-8"')
        self.failUnlessEqual(out.get_payload(),
                             "Here's some encoded t=C3=A9xt.")

    def testEncodedHeaders(self):
        # Headers are encoded automatically, email headers are encoded
        # piece-wise to ensure the adresses remain ASCII
        mfrom = "Jos\xc3\xa9 Andr\xc3\xa9s <jose@example.com>"
        mto = "Ferran Adri\xc3\xa0 <ferran@example.com>"
        subject = "\xc2\xbfEsferificaci\xc3\xb3n?"
        mailhost = self._makeOne('MailHost')
        mailhost.send(messageText='A message.', mto=mto, mfrom=mfrom,
                      subject=subject, charset='utf-8')
        out = message_from_string(mailhost.sent)
        self.failUnlessEqual(out['To'],
                         '=?utf-8?q?Ferran_Adri=C3=A0?= <ferran@example.com>')
        self.failUnlessEqual(out['From'],
                             '=?utf-8?q?Jos=C3=A9_Andr=C3=A9s?= <jose@example.com>')
        self.failUnlessEqual(out['Subject'],
                             '=?utf-8?q?=C2=BFEsferificaci=C3=B3n=3F?=')
        # utf-8 will default to Quoted Printable encoding
        self.failUnlessEqual(out['Content-Transfer-Encoding'],
                             'quoted-printable')
        self.failUnlessEqual(out['Content-Type'], 'text/plain; charset="utf-8"')
        self.failUnlessEqual(out.get_payload(), "A message.")

    def testAlreadyEncodedMessage(self):
        # If the message already specifies encodings, it is
        # essentially not altered this is true even if charset or
        # msg_type is specified
        msg = """\
From: =?utf-8?q?Jos=C3=A9_Andr=C3=A9s?= <jose@example.com>
To: =?utf-8?q?Ferran_Adri=C3=A0?= <ferran@example.com>
Subject: =?utf-8?q?=C2=BFEsferificaci=C3=B3n=3F?=
Date: Sun, 27 Aug 2006 17:00:00 +0200
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: base64
MIME-Version: 1.0 (Generated by testMailHost.py)

wqFVbiB0cnVjbyA8c3Ryb25nPmZhbnTDoXN0aWNvPC9zdHJvbmc+IQ=3D=3D
"""
        mailhost = self._makeOne('MailHost')
        mailhost.send(messageText=msg)
        self.failUnlessEqual(mailhost.sent, msg)
        mailhost.send(messageText=msg, msg_type='text/plain')
        # The msg_type is ignored if already set
        self.failUnlessEqual(mailhost.sent, msg)

    def testAlreadyEncodedMessageWithCharset(self):
        # If the message already specifies encodings, it is
        # essentially not altered this is true even if charset or
        # msg_type is specified
        msg = """\
From: =?utf-8?q?Jos=C3=A9_Andr=C3=A9s?= <jose@example.com>
To: =?utf-8?q?Ferran_Adri=C3=A0?= <ferran@example.com>
Subject: =?utf-8?q?=C2=BFEsferificaci=C3=B3n=3F?=
Date: Sun, 27 Aug 2006 17:00:00 +0200
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: base64
MIME-Version: 1.0 (Generated by testMailHost.py)

wqFVbiB0cnVjbyA8c3Ryb25nPmZhbnTDoXN0aWNvPC9zdHJvbmc+IQ=3D=3D
"""
        mailhost = self._makeOne('MailHost')
        # Pass a different charset, which will apply to any explicitly
        # set headers
        mailhost.send(messageText=msg,
                      subject='\xbfEsferificaci\xf3n?',
                      charset='iso-8859-1', msg_type='text/plain')
        # The charset for the body should remain the same, but any
        # headers passed into the method will be encoded using the
        # specified charset
        out = message_from_string(mailhost.sent)
        self.failUnlessEqual(out['Content-Type'], 'text/html; charset="utf-8"')
        self.failUnlessEqual(out['Content-Transfer-Encoding'],
                                 'base64')
        # Headers set by parameter will be set using charset parameter
        self.failUnlessEqual(out['Subject'],
                             '=?iso-8859-1?q?=BFEsferificaci=F3n=3F?=')
        # original headers will be unaltered
        self.failUnlessEqual(out['From'],
                             '=?utf-8?q?Jos=C3=A9_Andr=C3=A9s?= <jose@example.com>')

    def testUnicodeMessage(self):
        # unicode messages and headers are decoded using the given charset
        msg = unicode("Here's some unencoded <strong>t\xc3\xa9xt</strong>.",
                      'utf-8')
        mfrom = unicode('Ferran Adri\xc3\xa0 <ferran@example.com>', 'utf-8')
        subject = unicode('\xc2\xa1Andr\xc3\xa9s!', 'utf-8')
        mailhost = self._makeOne('MailHost')
        mailhost.send(messageText=msg,
                      mto='"Name, Nick" <recipient@domain.com>',
                      mfrom=mfrom, subject=subject, charset='utf-8',
                      msg_type='text/html')
        out = message_from_string(mailhost.sent)
        self.failUnlessEqual(out['To'],
                         '"Name, Nick" <recipient@domain.com>')
        self.failUnlessEqual(out['From'],
                             '=?utf-8?q?Ferran_Adri=C3=A0?= <ferran@example.com>')
        self.failUnlessEqual(out['Subject'], '=?utf-8?q?=C2=A1Andr=C3=A9s!?=')
        self.failUnlessEqual(out['Content-Transfer-Encoding'], 'quoted-printable')
        self.failUnlessEqual(out['Content-Type'], 'text/html; charset="utf-8"')
        self.failUnlessEqual(out.get_payload(),
                             "Here's some unencoded <strong>t=C3=A9xt</strong>.")

    def testUnicodeNoEncodingErrors(self):
        # Unicode messages and headers raise errors if no charset is passed to
        # send
        msg = unicode("Here's some unencoded <strong>t\xc3\xa9xt</strong>.",
                      'utf-8')
        subject = unicode('\xc2\xa1Andr\xc3\xa9s!', 'utf-8')
        mailhost = self._makeOne('MailHost')
        self.assertRaises(UnicodeEncodeError,
                          mailhost.send, msg,
                          mto='"Name, Nick" <recipient@domain.com>',
                          mfrom='Foo Bar <foo@domain.com>',
                          subject=subject)

    def testUnicodeDefaultEncoding(self):
        # However if we pass unicode that can be encoded to the
        # default encoding (generally 'us-ascii'), no error is raised.
        # We include a date in the messageText to make inspecting the
        # results more convenient.
        msg = u"""\
Date: Sun, 27 Aug 2006 17:00:00 +0200

Here's some unencoded <strong>text</strong>."""
        subject = u'Andres!'
        mailhost = self._makeOne('MailHost')
        mailhost.send(msg, mto=u'"Name, Nick" <recipient@domain.com>',
                      mfrom=u'Foo Bar <foo@domain.com>', subject=subject)
        out = mailhost.sent
        # Ensure the results are not unicode
        self.failUnlessEqual(out,"""\
Date: Sun, 27 Aug 2006 17:00:00 +0200
Subject: Andres!
To: "Name, Nick" <recipient@domain.com>
From: Foo Bar <foo@domain.com>

Here's some unencoded <strong>text</strong>.""")
        self.failUnlessEqual(type(out), str)

    def testSendMessageObject(self):
        # send will accept an email.Message.Message object directly
        msg = message_from_string("""\
From: =?utf-8?q?Jos=C3=A9_Andr=C3=A9s?= <jose@example.com>
To: =?utf-8?q?Ferran_Adri=C3=A0?= <ferran@example.com>
Subject: =?utf-8?q?=C2=BFEsferificaci=C3=B3n=3F?=
Date: Sun, 27 Aug 2006 17:00:00 +0200
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: base64
MIME-Version: 1.1

wqFVbiB0cnVjbyA8c3Ryb25nPmZhbnTDoXN0aWNvPC9zdHJvbmc+IQ=3D=3D
""")
        mailhost = self._makeOne('MailHost')
        mailhost.send(msg)
        out = message_from_string(mailhost.sent)
        self.failUnlessEqual(out.as_string(), msg.as_string())

        # we can even alter a from and subject headers without affecting the
        # original object
        mailhost.send(msg, mfrom='Foo Bar <foo@domain.com>', subject='Changed!')
        out = message_from_string(mailhost.sent)

        # We need to make sure we didn't mutate the message we were passed
        self.failIfEqual(out.as_string(), msg.as_string())
        self.failUnlessEqual(out['From'], 'Foo Bar <foo@domain.com>')
        self.failUnlessEqual(msg['From'],
                             '=?utf-8?q?Jos=C3=A9_Andr=C3=A9s?= <jose@example.com>')
        # The subject is encoded with the body encoding since no
        # explicit encoding was specified
        self.failUnlessEqual(out['Subject'], '=?utf-8?q?Changed!?=')
        self.failUnlessEqual(msg['Subject'],
                             '=?utf-8?q?=C2=BFEsferificaci=C3=B3n=3F?=')

    def testExplicitUUEncoding(self):
        # We can request a payload encoding explicitly, though this
        # should probably be considered deprecated functionality.
        mailhost = self._makeOne('MailHost')
        # uuencoding
        mailhost.send('Date: Sun, 27 Aug 2006 17:00:00 +0200\n\nA Message',
                      mfrom='sender@domain.com',
                      mto='Foo Bar <foo@domain.com>', encode='uue')
        out = message_from_string(mailhost.sent)
        self.failUnlessEqual(mailhost.sent, """\
Date: Sun, 27 Aug 2006 17:00:00 +0200
Subject: [No Subject]
To: Foo Bar <foo@domain.com>
From: sender@domain.com
Content-Transfer-Encoding: uue
Mime-Version: 1.0

begin 666 -
)02!-97-S86=E
 
end
""")

    def testExplicitBase64Encoding(self):
        mailhost = self._makeOne('MailHost')
        mailhost.send('Date: Sun, 27 Aug 2006 17:00:00 +0200\n\nA Message',
                      mfrom='sender@domain.com',
                      mto='Foo Bar <foo@domain.com>', encode='base64')
        out = message_from_string(mailhost.sent)
        self.failUnlessEqual(mailhost.sent, """\
Date: Sun, 27 Aug 2006 17:00:00 +0200
Subject: [No Subject]
To: Foo Bar <foo@domain.com>
From: sender@domain.com
Content-Transfer-Encoding: base64
Mime-Version: 1.0

QSBNZXNzYWdl""")

    def testExplicit7bitEncoding(self):
        mailhost = self._makeOne('MailHost')
        mailhost.send('Date: Sun, 27 Aug 2006 17:00:00 +0200\n\nA Message',
                      mfrom='sender@domain.com',
                      mto='Foo Bar <foo@domain.com>', encode='7bit')
        out = message_from_string(mailhost.sent)
        self.failUnlessEqual(mailhost.sent, """\
Date: Sun, 27 Aug 2006 17:00:00 +0200
Subject: [No Subject]
To: Foo Bar <foo@domain.com>
From: sender@domain.com
Content-Transfer-Encoding: 7bit
Mime-Version: 1.0

A Message""")

    def testExplicit8bitEncoding(self):
        mailhost = self._makeOne('MailHost')
        # We pass an encoded string with unspecified charset, it should be
        # encoded 8bit
        mailhost.send('Date: Sun, 27 Aug 2006 17:00:00 +0200\n\nA M\xc3\xa9ssage',
                      mfrom='sender@domain.com',
                      mto='Foo Bar <foo@domain.com>', encode='8bit')
        out = message_from_string(mailhost.sent)
        self.failUnlessEqual(mailhost.sent, """\
Date: Sun, 27 Aug 2006 17:00:00 +0200
Subject: [No Subject]
To: Foo Bar <foo@domain.com>
From: sender@domain.com
Content-Transfer-Encoding: 8bit
Mime-Version: 1.0

A M\xc3\xa9ssage""")

    def testSendTemplate(self):
        content = FakeContent('my_template', 'A Message')
        mailhost = self._makeOne('MailHost')
        result = mailhost.sendTemplate(content, 'my_template',
                                       mto='Foo Bar <foo@domain.com>',
                                       mfrom='sender@domain.com')
        self.failUnlessEqual(result, 'SEND OK')
        result = mailhost.sendTemplate(content, 'my_template',
                                       mto='Foo Bar <foo@domain.com>',
                                       mfrom='sender@domain.com',
                                       statusTemplate='wrong_name')
        self.failUnlessEqual(result, 'SEND OK')
        result = mailhost.sendTemplate(content, 'my_template',
                                       mto='Foo Bar <foo@domain.com>',
                                       mfrom='sender@domain.com',
                                       statusTemplate='check_status')
        self.failUnlessEqual(result, 'Message Sent')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestMailHost ) )
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
