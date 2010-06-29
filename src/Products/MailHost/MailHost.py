##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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
import logging
from os.path import realpath
import re
from cStringIO import StringIO
from copy import deepcopy
from email.Header import Header
from email.Charset import Charset
from email import message_from_string
from email.Message import Message
from email import Encoders
try:
    import email.utils as emailutils
except ImportError:
    import email.Utils as emailutils
import email.Charset
# We import from a private module here because the email module
# doesn't provide a good public address list parser
import uu

from threading import Lock
import time

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.Permissions import change_configuration, view
from AccessControl.Permissions import use_mailhost_services
from Acquisition import Implicit
from App.special_dtml import DTMLFile
from DateTime.DateTime import DateTime
from Persistence import Persistent
from OFS.role import RoleManager
from OFS.SimpleItem import Item

from zope.interface import implements
from zope.sendmail.mailer import SMTPMailer
from zope.sendmail.maildir import Maildir
from zope.sendmail.delivery import DirectMailDelivery, QueuedMailDelivery, \
                            QueueProcessorThread

from interfaces import IMailHost
from decorator import synchronized

queue_threads = {}  # maps MailHost path -> queue processor threada

LOG = logging.getLogger('MailHost')

# Encode utf-8 emails as Quoted Printable by default
email.Charset.add_charset("utf-8", email.Charset.QP, email.Charset.QP, "utf-8")
formataddr = emailutils.formataddr
parseaddr = emailutils.parseaddr
getaddresses = emailutils.getaddresses
CHARSET_RE = re.compile('charset=[\'"]?([\w-]+)[\'"]?', re.IGNORECASE)

class MailHostError(Exception):
    pass

manage_addMailHostForm = DTMLFile('dtml/addMailHost_form', globals())
def manage_addMailHost(self,
                       id,
                       title='',
                       smtp_host='localhost',
                       localhost='localhost',
                       smtp_port=25,
                       timeout=1.0,
                       REQUEST=None,
                      ):
    """ Add a MailHost into the system.
    """
    i = MailHost( id, title, smtp_host, smtp_port )   #create new mail host
    self._setObject( id,i )   #register it

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')

add = manage_addMailHost


class MailBase(Implicit, Item, RoleManager):
    """a mailhost...?"""

    implements(IMailHost)

    meta_type = 'Mail Host'
    manage = manage_main = DTMLFile('dtml/manageMailHost', globals())
    manage_main._setName('manage_main')
    index_html = None
    security = ClassSecurityInfo()
    smtp_uid = '' # Class attributes for smooth upgrades
    smtp_pwd = ''
    smtp_queue = False
    smtp_queue_directory = '/tmp'
    force_tls = False
    lock = Lock()

    # timeout = 1.0 # unused?

    manage_options = (
        (
        {'icon':'', 'label':'Edit',
         'action':'manage_main',
         'help':('MailHost','Mail-Host_Edit.stx')},
        )
        + RoleManager.manage_options
        + Item.manage_options
        )


    def __init__(self,
                 id='',
                 title='',
                 smtp_host='localhost',
                 smtp_port=25, 
                 force_tls=False, 
                 smtp_uid='',
                 smtp_pwd='',
                 smtp_queue=False,
                 smtp_queue_directory='/tmp',
                ):
        """Initialize a new MailHost instance.
        """
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
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    security.declareProtected(change_configuration, 'manage_makeChanges')
    def manage_makeChanges(self,
                           title,
                           smtp_host,
                           smtp_port,
                           smtp_uid='',
                           smtp_pwd='', 
                           smtp_queue=False,
                           smtp_queue_directory='/tmp',
                           force_tls=False, 
                           REQUEST=None,
                          ):
        """Make the changes.
        """
        title = str(title)
        smtp_host = str(smtp_host)
        smtp_port = int(smtp_port)

        self.title = title
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
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
    def sendTemplate(trueself,
                     self,
                     messageTemplate,
                     statusTemplate=None,
                     mto=None,
                     mfrom=None,
                     encode=None,
                     REQUEST=None,
                     immediate=False,
                     charset=None,
                     msg_type=None,
                    ):
        """Render a mail template, then send it...
        """
        mtemplate = getattr(self, messageTemplate)
        messageText = mtemplate(self, trueself.REQUEST)
        trueself.send(messageText, mto=mto, mfrom=mfrom,
                      encode=encode, immediate=immediate,
                      charset=charset, msg_type=msg_type)

        if not statusTemplate:
            return "SEND OK"
        try:
            stemplate = getattr(self, statusTemplate)
            return stemplate(self, trueself.REQUEST)
        except:
            return "SEND OK"

    security.declareProtected(use_mailhost_services, 'send')
    def send(self,
             messageText,
             mto=None,
             mfrom=None,
             subject=None,
             encode=None,
             immediate=False,
             charset=None,
             msg_type=None,
            ):
        messageText, mto, mfrom = _mungeHeaders(messageText, mto, mfrom,
                                                subject, charset, msg_type)
        # This encode step is mainly for BBB, encoding should be
        # automatic if charset is passed.  The automated charset-based
        # encoding will be preferred if both encode and charset are
        # provided.
        messageText = _encode(messageText, encode)
        self._send(mfrom, mto, messageText, immediate)

    # This is here for backwards compatibility only. Possibly it could
    # be used to send messages at a scheduled future time, or via a mail queue?
    security.declareProtected(use_mailhost_services, 'scheduledSend')
    scheduledSend = send

    security.declareProtected(use_mailhost_services, 'simple_send')
    def simple_send(self, mto, mfrom, subject, body, immediate=False):
        body = "From: %s\nTo: %s\nSubject: %s\n\n%s" % (
            mfrom, mto, subject, body)

        self._send(mfrom, mto, body, immediate)


    def _makeMailer(self):
        """ Create a SMTPMailer """
        return SMTPMailer(hostname=self.smtp_host,
                          port=int(self.smtp_port),
                          username=self.smtp_uid or None,
                          password=self.smtp_pwd or None,
                          force_tls=self.force_tls
                         )

    security.declarePrivate('_getThreadKey')
    def _getThreadKey(self):
        """ Return the key used to find our processor thread.
        """
        return realpath(self.smtp_queue_directory)

    @synchronized(lock)
    def _stopQueueProcessorThread(self):
        """ Stop thread for processing the mail queue.
        """
        key = self._getThreadKey()
        if queue_threads.has_key(key):
            thread = queue_threads[key]
            thread.stop()
            while thread.isAlive():
                # wait until thread is really dead
                time.sleep(0.3)
            del queue_threads[key]
            LOG.info('Thread for %s stopped' % key)

    @synchronized(lock)
    def _startQueueProcessorThread(self):
        """ Start thread for processing the mail queue.
        """
        key = self._getThreadKey()
        if not queue_threads.has_key(key):
            thread = QueueProcessorThread()
            thread.setMailer(self._makeMailer())
            thread.setQueuePath(self.smtp_queue_directory)
            thread.start()
            queue_threads[key] = thread     
            LOG.info('Thread for %s started' % key)

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
        """ return True/False is queue thread is working
        """
        th = queue_threads.get(self._getThreadKey())
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
    def _send(self, mfrom, mto, messageText, immediate=False):
        """ Send the message """

        if immediate:
            self._makeMailer().send(mfrom, mto, messageText)
        else:
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

def uu_encoder(msg):
    """For BBB only, don't send uuencoded emails"""
    orig = StringIO(msg.get_payload())
    encdata = StringIO()
    uu.encode(orig, encdata)
    msg.set_payload(encdata.getvalue())

# All encodings supported by mimetools for BBB
ENCODERS = {
    'base64': Encoders.encode_base64,
    'quoted-printable': Encoders.encode_quopri,
    '7bit': Encoders.encode_7or8bit,
    '8bit': Encoders.encode_7or8bit,
    'x-uuencode': uu_encoder,
    'uuencode':  uu_encoder,
    'x-uue': uu_encoder,
    'uue': uu_encoder,
    }

def _encode(body, encode=None):
    """Manually sets an encoding and encodes the message if not
    already encoded."""
    if encode is None:
        return body
    mo = message_from_string(body)
    current_coding = mo['Content-Transfer-Encoding']
    if current_coding == encode:
        # already encoded correctly, may have been automated
        return body
    if mo['Content-Transfer-Encoding'] not in ['7bit', None]:
        raise MailHostError, 'Message already encoded'
    if encode in ENCODERS:
        ENCODERS[encode](mo)
        if not mo['Content-Transfer-Encoding']:
            mo['Content-Transfer-Encoding'] =  encode
        if not mo['Mime-Version']:
            mo['Mime-Version'] =  '1.0'
    return mo.as_string()

def _mungeHeaders(messageText, mto=None, mfrom=None, subject=None,
                  charset=None, msg_type=None):
    """Sets missing message headers, and deletes Bcc.
       returns fixed message, fixed mto and fixed mfrom"""
    # If we have been given unicode fields, attempt to encode them
    if isinstance(messageText, unicode):
        messageText = _try_encode(messageText, charset)
    if isinstance(mto, unicode):
        mto = _try_encode(mto, charset)
    if isinstance(mfrom, unicode):
        mfrom = _try_encode(mfrom, charset)
    if isinstance(subject, unicode):
        subject = _try_encode(subject, charset)

    if isinstance(messageText, Message):
        # We already have a message, make a copy to operate on
        mo = deepcopy(messageText)
    else:
        # Otherwise parse the input message
        mo = message_from_string(messageText)

    if msg_type and not mo.get('Content-Type'):
        # we don't use get_content_type because that has a default
        # value of 'text/plain'
        mo.set_type(msg_type)
    if not mo.is_multipart():
        charset_match = CHARSET_RE.search(mo['Content-Type'] or '')
        if charset and not charset_match:
            # Don't change the charset if already set
            # This encodes the payload automatically based on the default
            # encoding for the charset
            mo.set_charset(charset)
        elif charset_match and not charset:
            # If a charset parameter was provided use it for header encoding below,
            # Otherwise, try to use the charset provided in the message.
            charset = charset_match.groups()[0]
    else:
        # Do basically the same for each payload as for the complete
        # multipart message.
        for index, payload in enumerate(mo.get_payload()):
            if not isinstance(payload, Message):
                payload = message_from_string(payload)
            charset_match = CHARSET_RE.search(payload['Content-Type'] or '')
            if payload.get_filename() is None:
                # No binary file
                if charset and not charset_match:
                    payload.set_charset(charset)
                elif charset_match and not charset:
                    charset = charset_match.groups()[0]
            mo.get_payload()[index] = payload

    # Parameters given will *always* override headers in the messageText.
    # This is so that you can't override or add to subscribers by adding
    # them to # the message text.
    if subject:
        # remove any existing header otherwise we get two
        del mo['Subject']
        # Perhaps we should ignore errors here and pass 8bit strings
        # on encoding errors
        mo['Subject'] = Header(subject, charset, errors='replace')
    elif not mo.get('Subject'):
        mo['Subject'] = '[No Subject]'

    if mto:
        if isinstance(mto, basestring):
            mto = [formataddr(addr) for addr in getaddresses((mto,))]
        if not mo.get('To'):
            mo['To'] = ', '.join(str(_encode_address_string(e, charset))
                                 for e in mto)
    else:
        # If we don't have recipients, extract them from the message
        mto = []
        for header in ('To', 'Cc', 'Bcc'):
            v = ','.join(mo.get_all(header) or [])
            if v:
                mto += [formataddr(addr) for addr in getaddresses((v,))]
        if not mto:
            raise MailHostError, "No message recipients designated"

    if mfrom:
        # XXX: do we really want to override an explicitly set From
        # header in the messageText
        del mo['From']
        mo['From'] = _encode_address_string(mfrom, charset)
    else:
        if mo.get('From') is None:
            raise MailHostError,"Message missing SMTP Header 'From'"
        mfrom = mo['From']

    if mo.get('Bcc'):
        del mo['Bcc']

    if not mo.get('Date'):
        mo['Date'] = DateTime().rfc822()

    return mo.as_string(), mto, mfrom

def _try_encode(text, charset):
    """Attempt to encode using the default charset if none is
    provided.  Should we permit encoding errors?"""
    if charset:
        return text.encode(charset)
    else:
        return text.encode()

def _encode_address_string(text, charset):
    """Split the email into parts and use header encoding on the name
    part if needed. We do this because the actual addresses need to be
    ASCII with no encoding for most SMTP servers, but the non-address
    parts should be encoded appropriately."""
    header = Header()
    name, addr = parseaddr(text)
    try:
        name.decode('us-ascii')
    except UnicodeDecodeError:
        if charset:
            charset = Charset(charset)
            name = charset.header_encode(name)
    # We again replace rather than raise an error or pass an 8bit string
    header.append(formataddr((name, addr)), errors='replace')
    return header
