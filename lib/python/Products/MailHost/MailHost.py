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
"""SMTP mail objects

$Id: MailHost.py,v 1.53 2000/06/19 18:51:58 brian Exp $"""
__version__ = "$Revision: 1.53 $"[11:-2]

from Globals import Persistent, HTMLFile, HTML, MessageDialog
from smtplib import SMTP
from AccessControl.Role import RoleManager
from operator import truth
import Acquisition, sys, string, types, mimetools
import OFS.SimpleItem, re, quopri, rfc822
import Globals
from cStringIO import StringIO

smtpError = "SMTP Error"
MailHostError = "MailHost Error"

addForm=HTMLFile('addMailHost_form', globals())
def add(self, id, title='', smtp_host=None,
        localhost='localhost', smtp_port=25,
        timeout=1.0, REQUEST=None):
    ' add a MailHost into the system '

    id=str(id)
    title=str(title)
    if smtp_host is not None:
        smtp_host=str(smtp_host)
    if type(smtp_port) is not type(1):
        smtp_port=string.atoi(smtp_port)

    i=MailHost()            #create new mail host
    i.id=id                 #give it id
    i.title=title           #title
    i._init(smtp_host=smtp_host, smtp_port=smtp_port)

    self=self.this()
    self._setObject(id,i)   #register it
    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')

class MailBase(Acquisition.Implicit, OFS.SimpleItem.Item, RoleManager):
    'a mailhost...?'
    meta_type='Mail Host'
    manage=manage_main=HTMLFile('manageMailHost', globals())
    index_html=None
    icon='misc_/MailHost/MHIcon'

    timeout=1.0

    manage_options=(
        (
        {'icon':'', 'label':'Edit',
         'action':'manage_main', 'target':'manage_main',
         'help':('MailHost','Mail-Host_Edit.stx')},
        )
        +OFS.SimpleItem.Item.manage_options
        +RoleManager.manage_options
        )

    __ac_permissions__=(
        ('View management screens', ('manage','manage_main')),
        ('Change configuration', ('manage_makeChanges',)),
        ('Use mailhost services',('',)),
        )
   
    def __init__(self):
        'nothing yet'
        pass

    def _init(self, smtp_host, smtp_port):
        self.smtp_host=smtp_host
        self.smtp_port=smtp_port

    def manage_makeChanges(self,title,smtp_host,smtp_port, REQUEST=None):
        'make the changes'

        title=str(title)
        smtp_host=str(smtp_host)
        if type(smtp_port) is not type(1):
            smtp_port=string.atoi(smtp_port)

        self.title=title
        self.smtp_host=smtp_host
        self.smtp_port=smtp_port
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
        headers = extractheaders(messageText)
        if mto: headers['to'] = mto
        if mfrom: headers['from'] = mfrom
        for requiredHeader in ('to', 'from'):
            if not headers.has_key(requiredHeader):
                raise MailHostError,"Message missing SMTP Header '%s'"\
                      % requiredHeader
        mailserver = SMTP(trueself.smtp_host, trueself.smtp_port)
        mailserver.sendmail(headers['from'], headers['to'], messageText)

        if not statusTemplate: return "SEND OK"

        try:
            stemplate=getattr(self, statusTemplate)
            return stemplate(self, trueself.REQUEST)
        except:
            return "SEND OK"

    def send(self, messageText, mto=None, mfrom=None, subject=None,
             encode=None):
        headers = extractheaders(messageText)
        
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
        smtpserver = SMTP(self.smtp_host, self.smtp_port)
        smtpserver.sendmail(headers['from'],headers['to'], messageText)

    def scheduledSend(self, messageText, mto=None, mfrom=None, subject=None,
                      encode=None):
        headers = extractheaders(messageText)

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
        smtpserver = SMTP(self.smtp_host, self.smtp_port)
        smtpserver.sendmail(headers['from'], headers['to'], messageText)

    def simple_send(self, mto, mfrom, subject, body):
        body="from: %s\nto: %s\nsubject: %s\n\n%s" % (
            mfrom, mto, subject, body)
        mailserver = SMTP(self.smtp_host, self.smtp_port)
        mailserver.sendmail(mfrom, mto, body)

        
Globals.default__class_init__(MailBase)

class MailHost(Persistent, MailBase):
    "persistent version"

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


def extractheaders(message):
    # return headers of message
    mfile=StringIO(message)
    mo=rfc822.Message(mfile)

    hd={}
    hd['to']=[]
    for header in (mo.getaddrlist('to'),
                   mo.getaddrlist('cc'),
                   mo.getaddrlist('bcc')):
        if not header: continue
        for name, addr in header:
            hd['to'].append(addr)
    
    hd['from']=mo.getaddr('from')[1]
    hd['subject']=mo.getheader('subject') or "No Subject"
    return hd
