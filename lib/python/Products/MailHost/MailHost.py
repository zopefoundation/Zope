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
"""MailHost, a Principia SMTP object"""

from Globals import Persistent, HTMLFile, HTML, MessageDialog
from socket import *; from select import select
from AccessControl.Role import RoleManager
from operator import truth
import Acquisition, sys, ts_regex, string, types, mimetools
import OFS.SimpleItem, re, quopri, rfc822
import Globals
from cStringIO import StringIO

#$Id: MailHost.py,v 1.42 1999/04/29 19:21:31 jim Exp $ 
__version__ = "$Revision: 1.42 $"[11:-2]
smtpError = "SMTP Error"
MailHostError = "MailHost Error"

addForm=HTMLFile('addMailHost_form', globals(), localhost=gethostname())
def add(self, id, title='', smtp_host=None, 
        localhost='localhost', smtp_port=25, timeout=1.0, REQUEST=None):
    ' add a MailHost into the system '
    i=MailHost()            #create new mail host
    i.id=id                 #give it id
    i.title=title           #title
    i._init(localHost=localhost, smtpHost=smtp_host, smtpPort=smtp_port,
            timeout=timeout)
    self._setObject(id,i)   #register it
    if REQUEST: return self.manage_main(self,REQUEST)


class MailBase(Acquisition.Implicit, OFS.SimpleItem.Item, RoleManager):
    'a mailhost...?'
    meta_type='Mail Host'
    manage=manage_main=HTMLFile('manageMailHost', globals())
    index_html=None
    icon='misc_/MailHost/MHIcon'

    timeout=1.0

    manage_options=({'icon':'', 'label':'Edit',
                     'action':'manage_main', 'target':'manage_main'},
                    {'icon':'', 'label':'Security',
                     'action':'manage_access', 'target':'manage_main'},
                   )

    __ac_permissions__=(
        ('View management screens', ('manage',)),
        ('Change configuration', ('manage_makeChanges',)),
        ('Use mailhost services',('',)),
        )
   
    def __init__(self):
        'nothing yet'
        pass

    def _init(self, localHost, smtpHost, smtpPort, timeout=1):
        self.localHost=localHost
        self.smtpHost=smtpHost
        self.smtpPort=smtpPort
        self.timeout=timeout

    def manage_makeChanges(self,title,localHost,smtpHost,smtpPort,
                           timeout, REQUEST=None):
        'make the changes'
        self.title=title
        self.localHost=localHost
        self.smtpHost=smtpHost
        self.smtpPort=smtpPort
        self.timeout=timeout
        if REQUEST: return MessageDialog(
            title  ='Changed %s' % self.__name__,
            message='%s has been updated' % self.id,
            action =REQUEST['URL2']+'/manage_main',
            target ='manage_main')
    
    def sendTemplate(trueself, self, messageTemplate, 
                     statusTemplate=None, mto=None, mfrom=None,
                     encode=None, REQUEST=None):
        'render a mail template, then send it...'
        mtemplate = getattr(self, messageTemplate)
        messageText = mtemplate(self, trueself.REQUEST)
        messageText=_encode(messageText, encode)
        headers, message = decapitate(messageText)
        if mto: headers['to'] = mto
        if mfrom: headers['from'] = mfrom
        for requiredHeader in ('to', 'from'):
            if not headers.has_key(requiredHeader):
                raise MailHostError,"Message missing SMTP Header '%s'"\
                      % requiredHeader
        Send(trueself.smtpHost, trueself.smtpPort, 
             trueself.localHost, trueself.timeout, 
             headers['from'], headers['to'],
             headers['subject'] or 'No Subject', messageText
             )

        if not statusTemplate: return "SEND OK"

        try:
            stemplate=getattr(self, statusTemplate)
            return stemplate(self, trueself.REQUEST)
        except:
            return "SEND OK"

    def send(self, messageText, mto=None, mfrom=None, subject=None,
             encode=None):
        headers, message = decapitate(messageText)
        
        if not headers['subject']:
            messageText="subject: %s\n%s" % (subject or '[No Subject]',
                                             messageText)
        if mto:
            if type(mto) is type('s'):
                mto=map(string.strip, string.split(mto,','))
            headers['to'] = filter(truth, mto)
        if mfrom:
            headers['from'] = mfrom
            
        for requiredHeader in ('to', 'from'):
            if not headers.has_key(requiredHeader):
                raise MailHostError,"Message missing SMTP Header '%s'"\
                % requiredHeader
        messageText=_encode(messageText, encode)
        sm=SendMail(self.smtpHost, self.smtpPort, self.localHost, self.timeout)
        sm.send(mfrom=headers['from'], mto=headers['to'],
                subj=headers['subject'] or 'No Subject',
                body=messageText)

    def scheduledSend(self, messageText, mto=None, mfrom=None, subject=None,
                      encode=None):
        headers, message = decapitate(messageText)

        if not headers['subject']:
            messageText="subject: %s\n%s" % (subject or '[No Subject]',
                                             messageText)
        if mto:
            if type(mto) is type('s'):
                mto=map(string.strip, string.split(mto,','))
            headers['to'] = filter(truth, mto)
        if mfrom:
            headers['from'] = mfrom

        for requiredHeader in ('to', 'from'):
            if not headers.has_key(requiredHeader):
                raise MailHostError,"Message missing SMTP Header '%s'"\
                % requiredHeader
        messageText=_encode(messageText, encode)
        Send(self.smtpHost, self.smtpPort, self.localHost, self.timeout,
             headers['from'], headers['to'],
             headers['subject'] or 'No Subject', messageText
             )

    def simple_send(self, mto, mfrom, subject, body):
        body="subject: %s\n\n%s" % (subject, body)
        SendMail(self.smtpHost, self.smtpPort, self.localHost,
                 self.timeout).send( 
                     mfrom=mfrom, mto=mto, subj=subject, body=body
                     )

class MailHost(Persistent, MailBase):
    "persistent version"

def Send(host, port, localhost, timeout, from_, to, subject, body):
    SendMail(host, port, localhost, timeout).send(from_, to, subject, body)
        
class SendMail:
    singledots=re.compile('^\.$', re.M)
    
    def __init__(self, smtpHost, smtpPort, localHost="localhost", timeout=1):
        self.conn = socket(AF_INET, SOCK_STREAM)
        self.conn.connect(smtpHost, smtpPort)
        self.timeout=timeout
        self.fd=self.conn.fileno()
        self.conn.send("helo "+localHost+"\015\012")
        while 1:
            if not self._check(): break

    def __del__(self):
        self._close()

    def getLine(self):
        line=''
        tm=self.timeout
        while 1:
            if not select([self.fd],[],[],tm)[0]:       #check the socket
                break
            data=self.conn.recv(1)
            if (not data) or (data == '\n'):
                break
            line=line+data
        return line

    def _check(self, lev='250'):
        line = self.getLine()
        if not line: return 0
        try:
            code=string.atoi(line[:3])
        except:
            raise smtpError, \
                  "Cannot convert line from SMTP: %s" % line
        if code > 400:
            raise smtpError, \
                  "Recieved error code %s from SMTP: %s"\
                  % (code, line)
        return 1

    def send(self, mfrom, mto, subj='No Subject', body='Blank Message'):
        self.conn.send("mail from:<%s>\015\012" % mfrom)
        self._check()
        if type(mto) in [types.ListType, types.TupleType]:
            for person in mto:
                self.conn.send("rcpt to:<%s>\015\012" % person)
                self._check()
        else:
            self.conn.send("rcpt to:<%s>\015\012" % mto)
            self._check()
        self.conn.send("data\015\012")
        self._check()
        body=self.singledots.sub('..', body)
        body=string.replace(body, '\r\n', '\n')
        body=string.replace(body, '\r', '\n')
        body=string.replace(body, '\n', '\015\012')
        self.conn.send(body)
        self.conn.send("\015\012.\015\012")
        self._check('354')

    def _close(self):
        self.conn.send("quit\015\012")
        self.conn.close()



def _encode(body, encode=None):
    if encode is None:
        return body
    mfile=StringIO(body)
    mo=mimetools.Message(mfile)
    if mo.getencoding() != '7bit': 
        raise MailHostError, 'Message already encoded'
    newmfile=StringIO()
    newmfile.write(string.joinfields(mo.headers, ''))
    newmfile.write('Content-Transfer-Encoding: %s\n' % encode)
    if not mo.has_key('Mime-Version'):
        newmfile.write('Mime-Version: 1.0\n')
    newmfile.write('\n')
    mimetools.encode(mfile, newmfile, encode)
    return newmfile.getvalue()


def decapitate(message):
    # split message into headers / body
    mfile=StringIO(message)
    mo=rfc822.Message(mfile)

    hd={}
    hd['to']=[]
    for header in (mo.getaddrlist('to'),
                   mo.getaddrlist('cc')):
        if not header: continue
        for name, addr in header:
            hd['to'].append(addr)
    
    hd['from']=mo.getaddr('from')[1]
    hd['subject']=mo.getheader('subject') or "No Subject"

    return hd, mfile.read()
