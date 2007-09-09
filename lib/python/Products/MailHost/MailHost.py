##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""SMTP mail objects

$Id$
"""

import mimetools
import rfc822
import time
import logging
from cStringIO import StringIO
from threading import Lock

import Acquisition
import OFS.SimpleItem
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import change_configuration, view
from AccessControl.Permissions import use_mailhost_services
from AccessControl.Permissions import view_management_screens
from AccessControl.Role import RoleManager
from Globals import Persistent, DTMLFile, InitializeClass
from DateTime import DateTime

from zope.interface import implements
from zope.sendmail.maildir import Maildir
from zope.sendmail.delivery import DirectMailDelivery, QueuedMailDelivery, \
                            QueueProcessorThread

from interfaces import IMailHost
from decorator import synchronized

# Use our own TLS/SSL-aware mailer since the zope.sendmail does
# not support TLS/SSL in this version (should be replaced with
# the next version)
from mailer import SMTPMailer

queue_threads = {}  # maps MailHost path -> queue processor threada

LOG = logging.getLogger('MailHost')

class MailHostError(Exception):
    pass

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
    """a mailhost...?"""

    implements(IMailHost)

    meta_type='Mail Host'
    manage=manage_main=DTMLFile('dtml/manageMailHost', globals())
    manage_main._setName('manage_main')
    index_html=None
    security = ClassSecurityInfo()
    smtp_uid='' # Class attributes for smooth upgrades
    smtp_pwd=''
    smtp_queue = False
    smtp_queue_directory = '/tmp'
    lock = Lock()

    # timeout=1.0 # unused?
    

    manage_options=(
        (
        {'icon':'', 'label':'Edit',
         'action':'manage_main',
         'help':('MailHost','Mail-Host_Edit.stx')},
        )
        +RoleManager.manage_options
        +OFS.SimpleItem.Item.manage_options
        )

    def __setstate__(self, state):
        import pdb; pdb.set_trace() 


    def __init__(self, id='', title='', smtp_host='localhost', smtp_port=25, 
                 force_tls=False, 
                 smtp_uid='', smtp_pwd='', smtp_queue=False, smtp_queue_directory='/tmp'):
        """Initialize a new MailHost instance """
        self.id = id
        self.title = title
        self.smtp_host = str( smtp_host )
        self.smtp_port = int(smtp_port)
        self.smtp_uid = smtp_uid
        self.smtp_pwd = smtp_pwd
        self.force_tls = force_tls
        self.smtp_queue = smtp_queue
        self.smtp_queue_directory = smtp_queue_directory


    # staying for now... (backwards compatibility)
    def _init(self, smtp_host, smtp_port):
        self.smtp_host=smtp_host
        self.smtp_port=smtp_port

    security.declareProtected(change_configuration, 'manage_makeChanges')
    def manage_makeChanges(self,title,smtp_host,smtp_port,smtp_uid='',smtp_pwd='', 
                           smtp_queue=False, smtp_queue_directory='/tmp',
                           force_tls=False, 
                           REQUEST=None):
        'make the changes'

        title=str(title)
        smtp_host=str(smtp_host)
        smtp_port=int(smtp_port)

        self.title=title
        self.smtp_host=smtp_host
        self.smtp_port=smtp_port
        self.smtp_uid = smtp_uid
        self.smtp_pwd = smtp_pwd
        self.force_tls = force_tls
        self.smtp_queue = smtp_queue
        self.smtp_queue_directory = smtp_queue_directory

        # restart queue processor thread 
        if self.smtp_queue:
            self._stopQueueProcessorThread() 
            self._startQueueProcessorThread() 
        else:
            self._stopQueueProcessorThread() 


        if REQUEST is not None:
            msg = 'MailHost %s updated' % self.id
            return self.manage_main( self
                                   , REQUEST
                                   , manage_tabs_message=msg
                                   )

    security.declareProtected(use_mailhost_services, 'sendTemplate')
    def sendTemplate(trueself, self, messageTemplate,
                     statusTemplate=None, mto=None, mfrom=None,
                     encode=None, REQUEST=None):
        'render a mail template, then send it...'
        mtemplate = getattr(self, messageTemplate)
        messageText = mtemplate(self, trueself.REQUEST)
        messageText, mto, mfrom = _mungeHeaders( messageText, mto, mfrom)
        messageText=_encode(messageText, encode)
        trueself._send(mfrom, mto, messageText)

        if not statusTemplate: return "SEND OK"

        try:
            stemplate=getattr(self, statusTemplate)
            return stemplate(self, trueself.REQUEST)
        except:
            return "SEND OK"

    security.declareProtected(use_mailhost_services, 'send')
    def send(self, messageText, mto=None, mfrom=None, subject=None,
             encode=None):

        messageText, mto, mfrom = _mungeHeaders( messageText, mto, mfrom, subject)
        messageText = _encode(messageText, encode)
        self._send(mfrom, mto, messageText)

    # This is here for backwards compatibility only. Possibly it could
    # be used to send messages at a scheduled future time, or via a mail queue?
    security.declareProtected(use_mailhost_services, 'scheduledSend')
    scheduledSend = send

    security.declareProtected(use_mailhost_services, 'simple_send')
    def simple_send(self, mto, mfrom, subject, body):
        body="From: %s\nTo: %s\nSubject: %s\n\n%s" % (
            mfrom, mto, subject, body)

        self._send( mfrom, mto, body )


    def _makeMailer(self):
        """ Create a SMTPMailer """
        return SMTPMailer(hostname=self.smtp_host,
                          port=int(self.smtp_port),
                          username=self.smtp_uid or None,
                          password=self.smtp_pwd or None,
                          force_tls=self.force_tls
                          )

    @synchronized(lock)
    def _stopQueueProcessorThread(self):
        """ Stop thread for processing the mail queue """

        path = self.absolute_url(1)
        if queue_threads.has_key(path):
            thread = queue_threads[path]
            thread.stop()
            while thread.isAlive():
                # wait until thread is really dead
                time.sleep(0.3)
            del queue_threads[path]
            LOG.info('Thread for %s stopped' % path)

    @synchronized(lock)
    def _startQueueProcessorThread(self):
        """ Start thread for processing the mail queue """
        
        path = self.absolute_url(1)
        if not queue_threads.has_key(path):
            thread = QueueProcessorThread()
            thread.setMailer(self._makeMailer())
            thread.setQueuePath(self.smtp_queue_directory)
            thread.start()
            queue_threads[path] = thread     
            LOG.info('Thread for %s started' % path)

     
    security.declareProtected(view, 'queueLength')
    def queueLength(self):
        """ return length of mail queue """

        try:
            maildir = Maildir(self.smtp_queue_directory)
            return len([item for item in maildir])
        except ValueError:
            return 'n/a - %s is not a maildir - please verify your ' \
                   'configuration' % self.smtp_queue_directory


    security.declareProtected(view, 'queueThreadAlive')
    def queueThreadAlive(self):
        """ return True/False is queue thread is working """

        th = queue_threads.get(self.absolute_url(1))
        if th:
            return th.isAlive()
        return False

    security.declareProtected(change_configuration, 'manage_restartQueueThread')
    def manage_restartQueueThread(self, action='start', REQUEST=None):
        """ Restart the queue processor thread """

        if action == 'stop':
            self._stopQueueProcessorThread()
        elif action == 'start':
            self._startQueueProcessorThread()
        else:
            raise ValueError('Unsupported action %s' % action)

        if REQUEST is not None:
            msg = 'Queue processor thread %s' % \
                  (action == 'stop' and 'stopped' or 'started')
            return self.manage_main(self, REQUEST, manage_tabs_message=msg)


    security.declarePrivate('_send')
    def _send(self, mfrom, mto, messageText):
        """ Send the message """

        if self.smtp_queue:
            # Start queue processor thread, if necessary
            self._startQueueProcessorThread()
            delivery = QueuedMailDelivery(self.smtp_queue_directory)
        else:
            delivery = DirectMailDelivery(self._makeMailer())

        delivery.send(mfrom, mto, messageText)                

InitializeClass(MailBase)


class MailHost(Persistent, MailBase):
    """persistent version"""


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
    mfile=StringIO(messageText.lstrip())
    mo=rfc822.Message(mfile)

    # Parameters given will *always* override headers in the messageText.
    # This is so that you can't override or add to subscribers by adding them to
    # the message text.
    if subject:
        mo['Subject'] = subject
    elif not mo.getheader('Subject'):
        mo['Subject'] = '[No Subject]'

    if mto:
        if isinstance(mto, basestring):
            mto = [rfc822.dump_address_pair(addr) for addr in rfc822.AddressList(mto) ]
        if not mo.getheader('To'):
            mo['To'] = ','.join(mto)
    else:
        mto = []
        for header in ('To', 'Cc', 'Bcc'):
            v = mo.getheader(header)
            if v:
                mto += [rfc822.dump_address_pair(addr) for addr in rfc822.AddressList(v)]
        if not mto:
            raise MailHostError, "No message recipients designated"

    if mfrom:
        mo['From'] = mfrom
    else:
        if mo.getheader('From') is None:
            raise MailHostError,"Message missing SMTP Header 'From'"
        mfrom = mo['From']

    if mo.getheader('Bcc'):
        mo.__delitem__('Bcc')

    if not mo.getheader('Date'):
        mo['Date'] = DateTime().rfc822()

    mo.rewindbody()
    finalmessage = mo
    finalmessage = mo.__str__() + '\n' + mfile.read()
    mfile.close()
    return finalmessage, mto, mfrom
