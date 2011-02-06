##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

def manage_addMailHost(id, title='', smtp_host=None,
        localhost='localhost', smtp_port=25,
        timeout=1.0):
    """

    Add a mailhost object to an ObjectManager.

    """


class MailHost:
    """

    MailHost objects work as adapters to Simple Mail Transfer Protocol
    (SMTP) servers.  MailHosts are used by DTML 'sendmail' tags
    to find the proper host to deliver mail to.

    """

    __constructor__=manage_addMailHost

    def send(messageText, mto=None, mfrom=None, subject=None,
             encode=None):
        """
        Sends an email message where the messageText is an rfc822 formatted
        message. This allows you complete control over the message headers,
        including setting any extra headers such as Cc: and Reply-To:.
        The arguments are:

            messageText -- The mail message. It can either be a rfc822
            formed text with header fields, or just a body without any
            header fields. The other arguments given will override the
            header fields in the message, if they exist.

            mto -- A commaseparated string or list of recipient(s) of the message.

            mfrom -- The address of the message sender.

            subject -- The subject of the message.

            encode -- The rfc822 defined encoding of the message.  The
            default of 'None' means no encoding is done.  Valid values
            are 'base64', 'quoted-printable' and 'uuencode'.

        """

    def simple_send(self, mto, mfrom, subject, body):
        """
        Sends a message. Only To:, From: and Subject: headers can be set.
        Note that simple_send does not process or validate its arguments
        in any way.
        The arguments are:

            mto -- A commaseparated string of recipient(s) of the message.

            mfrom -- The address of the message sender.

            subject -- The subject of the message.

            body -- The body of the message.
        """
