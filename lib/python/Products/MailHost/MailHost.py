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
"""SMTP mail objects
$Id: MailHost.py,v 1.74 2002/08/14 22:14:51 mj Exp $"""
__version__ = "$Revision: 1.74 $"[11:-2]

from Globals import Persistent, DTMLFile, InitializeClass
from smtplib import SMTP
from AccessControl.Role import RoleManager
from operator import truth
import Acquisition, sys, types, mimetools
import OFS.SimpleItem, re, quopri, rfc822
from cStringIO import StringIO
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens, \
                                      use_mailhost_services

smtpError = "SMTP Error"
MailHostError = "MailHost Error"

manage_addMailHostForm=DTMLFile('dtml/addMailHost_form', globals())
def manage_addMailHost( self, id, title='', smtp_host='localhost'
                      , localhost='localhost', smtp_port=25
                      , timeout=1.0, REQUEST=None ):
    ' add a MailHost into the system '
    i = MailHost( id, title, smtp_host, smtp_port )   #create new mail host
    self._setObject( id,i )   #register it

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')

add = manage_addMailHost

class MailBase(Acquisition.Implicit, OFS.SimpleItem.Item, RoleManager):
    'a mailhost...?'
    meta_type='Mail Host'
    manage=manage_main=DTMLFile('dtml/manageMailHost', globals())
    manage_main._setName('manage_main')
    index_html=None
    security = ClassSecurityInfo()

    timeout=1.0

    manage_options=(
        (
        {'icon':'', 'label':'Edit',
         'action':'manage_main',
         'help':('MailHost','Mail-Host_Edit.stx')},
        )
        +RoleManager.manage_options
        +OFS.SimpleItem.Item.manage_options
        )


    def __init__( self, id='', title='', smtp_host='localhost', smtp_port=25 ):
        """Initialize a new MailHost instance """
        self.id = id
        self.title = title
        self.smtp_host = str( smtp_host )
        self.smtp_port = int(smtp_port)


    # staying for now... (backwards compatibility)
    def _init(self, smtp_host, smtp_port):
        self.smtp_host=smtp_host
        self.smtp_port=smtp_port


    security.declareProtected( 'Change configuration', 'manage_makeChanges' )
    def manage_makeChanges(self,title,smtp_host,smtp_port, REQUEST=None):
        'make the changes'

        title=str(title)
        smtp_host=str(smtp_host)
        smtp_port=int(smtp_port)

        self.title=title
        self.smtp_host=smtp_host
        self.smtp_port=smtp_port
        if REQUEST is not None:
            msg = 'MailHost %s updated' % self.id
            return self.manage_main( self
                                   , REQUEST
                                   , manage_tabs_message=msg
                                   )


    security.declareProtected( use_mailhost_services, 'sendTemplate' )
    def sendTemplate(trueself, self, messageTemplate,
                     statusTemplate=None, mto=None, mfrom=None,
                     encode=None, REQUEST=None):
        'render a mail template, then send it...'
        mtemplate = getattr(self, messageTemplate)
        messageText = mtemplate(self, trueself.REQUEST)
        messageText, mto, mfrom = _mungeHeaders( messageText, mto, mfrom)
        messageText=_encode(messageText, encode)
        self._send(mfrom, mto, messageText)

        if not statusTemplate: return "SEND OK"

        try:
            stemplate=getattr(self, statusTemplate)
            return stemplate(self, trueself.REQUEST)
        except:
            return "SEND OK"


    security.declareProtected( use_mailhost_services, 'send' )
    def send(self, messageText, mto=None, mfrom=None, subject=None,
             encode=None):

        messageText, mto, mfrom = _mungeHeaders( messageText, mto, mfrom, subject)
        messageText = _encode(messageText, encode)
        self._send(mfrom, mto, messageText)


    # This is here for backwards compatibility only. Possibly it could
    # be used to send messages at a scheduled future time, or via a mail queue?
    security.declareProtected( use_mailhost_services, 'scheduledSend' )
    scheduledSend = send

    security.declareProtected( use_mailhost_services, 'simple_send' )
    def simple_send(self, mto, mfrom, subject, body):
        body="From: %s\nTo: %s\nSubject: %s\n\n%s" % (
            mfrom, mto, subject, body)

        self._send( mfrom, mto, body )


    security.declarePrivate( '_send' )
    def _send( self, mfrom, mto, messageText ):
        """ Send the message """
        smtpserver = SMTP( self.smtp_host, self.smtp_port )
        smtpserver.sendmail( mfrom, mto, messageText )
        smtpserver.quit()


InitializeClass( MailBase )

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
    newmfile.write(''.join(mo.headers))
    newmfile.write('Content-Transfer-Encoding: %s\n' % encode)
    if not mo.has_key('Mime-Version'):
        newmfile.write('Mime-Version: 1.0\n')
    newmfile.write('\n')
    mimetools.encode(mfile, newmfile, encode)
    return newmfile.getvalue()

def _mungeHeaders( messageText, mto=None, mfrom=None, subject=None):
    """Sets missing message headers, and deletes Bcc.
       returns fixed message, fixed mto and fixed mfrom"""
    mfile=StringIO(messageText.strip())
    mo=rfc822.Message(mfile)

    # Parameters given will *always* override headers in the messageText.
    # This is so that you can't override or add to subscribers by adding them to
    # the message text.
    if subject:
        mo['Subject'] = subject
    elif not mo.getheader('Subject'):
        mo['Subject'] = '[No Subject]'

    if mto:
        if isinstance(mto, types.StringType):
            mto=map(lambda x:x.strip(), mto.split(','))
        mo['To'] = ','.join(mto)
    else:
        if not mo.getheader('To'):
            raise MailHostError,"Message missing SMTP Header 'To'"
        mto = map(lambda x:x.strip(), mo['To'].split(','))
        if mo.getheader('Cc'):
            mto = mto + map(lambda x:x.strip(), mo['Cc'].split(','))
        if mo.getheader('Bcc'):
            mto = mto + map(lambda x:x.strip(), mo['Bcc'].split(','))

    if mfrom:
        mo['From'] = mfrom
    else:
        if mo.getheader('From') is None:
            raise MailHostError,"Message missing SMTP Header 'From'"
        mfrom = mo['From']

    if mo.getheader('Bcc'):
        mo.__delitem__('Bcc')

    mo.rewindbody()
    finalmessage = mo
    finalmessage = mo.__str__() + '\n' + mfile.read()
    mfile.close()
    return finalmessage, mto, mfrom
