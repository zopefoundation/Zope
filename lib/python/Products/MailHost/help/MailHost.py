##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
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
        Sends an email message.
        The arguments are:

          messageText -- The mail message. It can either be a rfc822 
          formed text with header fields, or just a body without any 
          header fields. The other arguments given will override the
          header fields in the message, if they exist.

          mto -- A string or list of recipient(s) of the message.

          mfrom -- The address of the message sender.

          subject -- The subject of the message.

          encode -- The rfc822 defined encoding of the message.  The
          default of 'None' means no encoding is done.  Valid values
          are 'base64', 'quoted-printable' and 'uuencode'.

        """


    
