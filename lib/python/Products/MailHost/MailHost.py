"""MailHost, a Principia SMTP object"""

from Globals import Persistent, HTMLFile, HTML, MessageDialog
from socket import *; from select import select
from AccessControl.Role import RoleManager
from operator import truth
import Acquisition, sys, ts_regex, string, types, rfc822
import OFS.SimpleItem
import Globals
from Scheduler.OneTimeEvent import OneTimeEvent
from ImageFile import ImageFile
from cStringIO import StringIO

#$Id: MailHost.py,v 1.31 1998/11/23 16:28:58 jim Exp $ 
__version__ = "$Revision: 1.31 $"[11:-2]
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
    ('View management screens', ['manage','manage_tabs']),
    ('Change permissions', ['manage_access']),
    ('Change configuration', ['manage_makeChanges']),
    ('Use mailhost services',['']),
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
		     statusTemplate=None, mto=None, mfrom=None, REQUEST):
        'render a mail template, then send it...'
	mtemplate = getattr(self, messageTemplate)
	messageText = mtemplate(self, trueself.REQUEST)

	headers, message = decapitate(messageText)
	if mto: headers['to'] = mto
	if mfrom: headers['from'] = mfrom
	for requiredHeader in ('to', 'from'):
	    if not headers.has_key(requiredHeader):
		raise MailHostError,"Message missing SMTP Header '%s'"\
		      % requiredHeader
        
	Globals.Scheduler.schedule(OneTimeEvent(
	    Send,
	    (trueself.smtpHost, trueself.smtpPort, 
	     trueself.localHost, trueself.timeout, 
	     headers['from'], headers['to'],
	     headers['subject'] or 'No Subject', messageText
	     ),
	    threadsafe=1
	    ))

	if not statusTemplate: return "SEND OK"

	try:
	    stemplate=getattr(self, statusTemplate)
	    return stemplate(self, trueself.REQUEST)
	except:
	    return "SEND OK"

    def send(self, messageText, mto=None, mfrom=None, subject=None):
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
    
        sm=SendMail(self.smtpHost, self.smtpPort, self.localHost, self.timeout)
	sm.send(mfrom=headers['from'], mto=headers['to'],
		subj=headers['subject'] or 'No Subject',
		body=messageText)

    def scheduledSend(self, messageText, mto=None, mfrom=None, subject=None):
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
 
	Globals.Scheduler.schedule(OneTimeEvent(
	    Send,
	    (self.smtpHost, self.smtpPort, self.localHost, self.timeout,
	     headers['from'], headers['to'],
	     headers['subject'] or 'No Subject', messageText
	     ),
	    threadsafe=1
	    ))

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
    def __init__(self, smtpHost, smtpPort, localHost="localhost", timeout=1):
        self.conn = socket(AF_INET, SOCK_STREAM)
        self.conn.connect(smtpHost, smtpPort)
	self.timeout=timeout
	self.fd=self.conn.fileno()
        self.conn.send("helo "+localHost+"\r\n")
	while 1:
	    if not self._check(): break

    def __del__(self):
        self._close()

    def getLine(self):
	line=''
	tm=self.timeout
	while 1:
	    if not select([self.fd],[],[],tm)[0]:	#check the socket
		break
	    data=self.conn.recv(1)
	    if (not data) or (data == '\n'):
		break
	    line=line+data
	return line

    def _check(self, lev='250'):
	line = self.getLine()
	if not line: return 0	#can't check an empty line, eh?
	try:
	    code=string.atoi(line[:3])
	except:
	    raise smtpError, "Cannot convert line from SMTP: %s" % line

	if code > 500:
	    raise smtpError, "Recieved error code %s from SMTP: %s"\
		  % (code, line)
	return 1

    def send(self, mfrom, mto, subj='No Subject', body='Blank Message'):
        self.conn.send("mail from:<%s>\n" % mfrom)
        self._check()
        if type(mto) in [types.ListType, types.TupleType]:
            for person in mto:
                self.conn.send("rcpt to:<%s>\n" % person)
                self._check()
        else:
            self.conn.send("rcpt to:<%s>\n" % mto)
            self._check()
        self.conn.send("data\n")
        self._check()
        self.conn.send(body)
        self.conn.send("\n.\n")
        self._check('354')

    def _close(self):
        self.conn.send("quit\n")
        self.conn.close()

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
