##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################
__rcs_id__='$Id: SendMailTag.py,v 1.4 1998/12/04 20:15:30 jim Exp $'
__version__='$Revision: 1.4 $'[11:-2]

from MailHost import MailBase
from DocumentTemplate.DT_Util import *
from DocumentTemplate.DT_String import String
from socket import gethostname
import string

class SendMailTag:
    '''the send mail tag, used like thus:

    <!--#sendmail someMailHostID-->
    to: person@their.machine.com
    from: me@mymachine.net
    subject: just called to say...

    boy howdy!
    <!--#/sendmail-->

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
    '''

    name='sendmail'
    blockContinuations=()

    def __init__(self, blocks):
        tname, args, section=blocks[0]
        args=parse_params(args, mailhost=None, mailto=None, mailfrom=None,
                          subject=None, smtphost=None, port='25')

        for key in ('mailto', 'mailfrom', 'subject', 'smtphost', 'port'):
            if not args.has_key(key):args[key]=''
        smtphost=None

        has_key=args.has_key
        if has_key('mailhost'): mailhost=args['mailhost']
        elif has_key('smtphost'): mailhost=smtphost=args['smtphost']
        elif has_key(''): mailhost=args['mailhost']=args['']
        else: raise MailHostError, 'No mailhost was specified in tag'

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
                   self.subject)

        return ' '

    __call__=render

String.commands['sendmail']=SendMailTag
