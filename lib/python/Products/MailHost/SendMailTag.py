##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
__rcs_id__='$Id: SendMailTag.py,v 1.8 2000/06/19 19:52:26 brian Exp $'
__version__='$Revision: 1.8 $'[11:-2]

from MailHost import MailBase
from DocumentTemplate.DT_Util import *
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
            mhost._init(localHost=gethostname(), smtpHost=self.smtphost,
                        smtpPort=self.port)

        mhost.send(self.section(md.this, md), self.mailto, self.mailfrom,
                   self.subject, self.encode)

        return ' '

    __call__=render

String.commands['sendmail']=SendMailTag
