import os, sys, unittest

import string, cStringIO, re
import ZODB, Acquisition
from Products.MailHost.MailHost import MailHostError, _mungeHeaders

class TestMailHost( unittest.TestCase ):

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
        resmsg, resto, resfrom = _mungeHeaders( msg, 'recipient@domain.com', 'sender@domain.com', 'This is the subject' )
        self.failUnless(resto == ['recipient@domain.com'])
        self.failUnless(resfrom == 'sender@domain.com' )

        # Add extra info
        resmsg, resto, resfrom = _mungeHeaders( msg, 'recipient2@domain.com', 'sender2@domain.com', 'This is the real subject' )
        self.failUnless(resto == ['recipient2@domain.com'])
        self.failUnless(resfrom == 'sender2@domain.com' )

    def testMissingHeaders( self ):
        msg = """X-Header: Dummy header

This is the message body."""
        # Doesn't specify to
        self.failUnlessRaises( MailHostError, _mungeHeaders, msg, mfrom='sender@domain.com' )
        # Doesn't specify from
        self.failUnlessRaises( MailHostError, _mungeHeaders, msg, mto='recipient@domain.com' )

    def testNoHeaders( self ):
        msg = """This is the message body."""
        # Doesn't specify to
        self.failUnlessRaises( MailHostError, _mungeHeaders, msg, mfrom='sender@domain.com' )
        # Doesn't specify from
        self.failUnlessRaises( MailHostError, _mungeHeaders, msg, mto='recipient@domain.com' )
        # Specify all
        resmsg, resto, resfrom = _mungeHeaders( msg, 'recipient2@domain.com', 'sender2@domain.com', 'This is the real subject' )
        self.failUnless(resto == ['recipient2@domain.com'])
        self.failUnless(resfrom == 'sender2@domain.com' )

    def testBCCHeader( self ):
        msg = "From: me@example.com\nBcc: many@example.com\n\nMessage text"
        # Specify only the "Bcc" header.  Useful for bulk emails.
        resmsg, resto, resfrom = _mungeHeaders(msg)
        self.failUnless(resto == ['many@example.com'])
        self.failUnless(resfrom == 'me@example.com' )


    def testAddressParser( self ):
        msg = """To: "Name, Nick" <recipient@domain.com>, "Foo Bar" <foo@domain.com>
CC: "Web, Jack" <jack@web.com>
From: sender@domain.com
Subject: This is the subject

This is the message body."""
        
        # Test Address-Parser for To & CC given in messageText
        
        resmsg, resto, resfrom = _mungeHeaders( msg )
        self.failUnless(resto == ['"Name, Nick" <recipient@domain.com>','"Foo Bar" <foo@domain.com>','"Web, Jack" <jack@web.com>'])
        self.failUnless(resfrom == 'sender@domain.com' )

        # Test Address-Parser for a given mto-string
        
        resmsg, resto, resfrom = _mungeHeaders( msg, mto= '"Public, Joe" <pjoe@domain.com>, "Foo Bar" <foo@domain.com>')

        self.failUnless(resto == ['"Public, Joe" <pjoe@domain.com>','"Foo Bar" <foo@domain.com>'])
        self.failUnless(resfrom == 'sender@domain.com' )

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestMailHost ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
