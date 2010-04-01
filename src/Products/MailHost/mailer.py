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

"""
SMTPMailer with TLS/SSL support
(original code taken from zope.sendmail)

$Id: mailer.py 78981 2007-08-19 06:38:48Z andreasjung $
"""
__docformat__ = 'restructuredtext'

import socket
from smtplib import SMTP

from zope.interface import implements
from zope.sendmail.interfaces import ISMTPMailer

have_ssl = hasattr(socket, 'ssl')

class SMTPMailer(object):

    implements(ISMTPMailer)

    smtp = SMTP

    def __init__(self, hostname='localhost', port=25,
                 username=None, password=None, no_tls=False, force_tls=False):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.force_tls = force_tls
        self.no_tls = no_tls

    def send(self, fromaddr, toaddrs, message):
        connection = self.smtp(self.hostname, str(self.port))

        # send EHLO
        code, response = connection.ehlo()
        if code < 200 or code >300:
            code, response = connection.helo()
            if code < 200 or code >300:
                raise RuntimeError('Error sending HELO to the SMTP server '
                                   '(code=%s, response=%s)' % (code, response))

        # encryption support
        have_tls =  connection.has_extn('starttls') 
        if not have_tls and self.force_tls:
            raise RuntimeError('TLS is not available but TLS is required')

        if have_tls and have_ssl and not self.no_tls: 
            connection.starttls()
            connection.ehlo()

        if connection.does_esmtp: 
            if self.username is not None and self.password is not None:
                connection.login(self.username, self.password)
        elif self.username:
            raise RuntimeError('Mailhost does not support ESMTP but a username '
                                'is configured')

        connection.sendmail(fromaddr, toaddrs, message)
        connection.quit()
