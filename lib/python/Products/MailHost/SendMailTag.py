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
__rcs_id__='$Id: SendMailTag.py,v 1.13 2001/11/28 15:50:59 matt Exp $'
__version__='$Revision: 1.13 $'[11:-2]

from MailHost import MailBase
from DocumentTemplate.DT_Util import parse_params,render_blocks
from DocumentTemplate.DT_String import String
from socket import gethostname
import string

class SendMailTag:
    '''the send mail tag, used like thus:

    <dtml-sendmail mailhost="someMailHostID">
    to: person@their.machine.com
    from: me@mymachine.net
    subject: just called to say...

    boy howdy!
    </dtml-sendmail>

    Text between the sendmail and /sendmail tags is processed
    by the MailHost machinery and delivered.  There must be at least
    one blank line seperating the headers (to/from/etc..) from the body
    of the message.

    Instead of specifying a MailHost, an smtphost may be specified
    ala 'smtphost="mail.mycompany.com" port=25' (port defaults to 25
    automatically).  Other parameters are

    * mailto -- person (or comma-seperated list of persons) to send the
    mail to.  If not specified, there **must** be a to: header in the
    message.

    * mailfrom -- person sending the mail (basically who the recipient can
    reply to).  If not specified, there **must** be a from: header in the
    message.

    * subject -- optional subject.  If not specified, there **must** be a
    subject: header in the message.

    * encode -- optional encoding. Possible values are: 'base64',
     'quoted-printable' and 'uuencode'.

    '''

    name='sendmail'
    blockContinuations=()
    encode=None

    def __init__(self, blocks):
        tname, args, section=blocks[0]
        args=parse_params(args, mailhost=None, mailto=None, mailfrom=None,
                          subject=None, smtphost=None, port='25',
                          encode=None)

        for key in ('mailto', 'mailfrom', 'subject', 'smtphost', 'port'):
            if not args.has_key(key):args[key]=''
        smtphost=None

        has_key=args.has_key
        if has_key('mailhost'): mailhost=args['mailhost']
        elif has_key('smtphost'): mailhost=smtphost=args['smtphost']
        elif has_key(''): mailhost=args['mailhost']=args['']
        else: raise MailHostError, 'No mailhost was specified in tag'

        if has_key('encode') and args['encode'] not in \
        ('base64', 'quoted-printable', 'uuencode', 'x-uuencode',
         'uue', 'x-uue'):
            raise MailHostError, (
                'An unsupported encoding was specified in tag')

        if not smtphost:
            self.__name__=self.mailhost=mailhost
            self.smtphost=None
        else:
            self.__name__=self.smtphost=smtphost
            self.mailhost=None
        self.section=section
        self.args=args
        self.mailto=args['mailto']
        self.mailfrom=args['mailfrom']
        self.subject=None or args['subject']
        if args['port'] and type(args['port']) is type('s'):
            self.port=args['port']=string.atoi(args['port'])
        elif args['port']=='':
            self.port=args['port']=25
        else:
            self.port=args['port']
        if has_key('encode'):
            self.encode=args['encode']
        else: self.encode=None

    def render(self, md):
        args=self.args
        has_key=args.has_key

        if self.mailhost:
            mhost=md[self.mailhost]
        elif self.smtphost:
            mhost=MailBase()
            mhost._init(self.smtphost, self.port)

        mhost.send(render_blocks(self.section.blocks, md),
                   self.mailto, self.mailfrom,
                   self.subject, self.encode
                   )

        return ' '

    __call__=render

String.commands['sendmail']=SendMailTag
