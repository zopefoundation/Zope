"""MailHost, a Principia SMTP object"""

from Globals import Persistent, HTMLFile, HTML, MessageDialog
from socket import *; from select import select
from AccessControl.Role import RoleManager
import Acquisition, sys, regex, string, types
import OFS.SimpleItem
import Globals
from Scheduler.OneTimeEvent import OneTimeEvent
from ImageFile import ImageFile

#$Id: MailHost.py,v 1.24 1998/01/05 19:34:12 jeffrey Exp $ 
__version__ = "$Revision: 1.24 $"[11:-2]
smtpError = "SMTP Error"
MailHostError = "MailHost Error"

addForm=HTMLFile('addMailHost_form', globals(), localhost=gethostname())
def add(self, id, title='', smtp_host=None, 
        localhost='localhost', smtp_port=25, REQUEST=None):
    ' add a MailHost into the system '
    i=MailHost()            #create new mail host
    i.id=id                 #give it id
    i.title=title           #title
    i._init(localHost=localhost, smtpHost=smtp_host, smtpPort=smtp_port)
    self._setObject(id,i)   #register it
    if REQUEST: return self.manage_main(self,REQUEST)


class MailBase(Acquisition.Implicit, OFS.SimpleItem.Item, RoleManager):
    'a mailhost...?'
    meta_type='Mail Host'
    manage=manage_main=HTMLFile('manageMailHost', globals())
    index_html=None
    icon='misc_/MailHost/MHIcon'

    manage_options=({'icon':'', 'label':'Edit',
		     'action':'manage_main', 'target':'manage_main',
	            },
		    {'icon':'', 'label':'Security',
		     'action':'manage_access', 'target':'manage_main',
		    },
		   )

    __ac_permissions__=(
    ('View management screens', ['manage','manage_tabs']),
    ('Change permissions', ['manage_access']),
    ('Change configuration', ['manage_makeChanges']),
    ('Use mailhost services',['']),
    )
   
    __ac_types__=(('Full Access', map(lambda x: x[0], __ac_permissions__)),
		 )


    def __init__(self):
        'nothing yet'
        pass

    def _init(self, localHost, smtpHost, smtpPort):
        self.localHost=localHost
        self.smtpHost=smtpHost
        self.smtpPort=smtpPort
        self.sentMessages=0

    def manage_makeChanges(self,title,localHost,smtpHost,smtpPort,
			   REQUEST=None):
        'make the changes'
        self.title=title
        self.localHost=localHost
        self.smtpHost=smtpHost
        self.smtpPort=smtpPort
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

	headers, message = newDecapitate(messageText)
	if mto: headers['to'] = mto
	if mfrom: headers['from'] = mfrom
	for requiredHeader in ('to', 'from', 'subject'):
	    if not headers.has_key(requiredHeader):
		raise MailHostError,"Message missing SMTP Header '%s'"\
		      % requiredHeader
        
	Globals.Scheduler.schedule(OneTimeEvent(
	    Send,
	    (trueself.smtpHost, trueself.smtpPort, 
	     trueself.localHost,
	     headers['from'], headers['to'],
	     headers['subject'], messageText
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
	if subject: messageText="subject: %s\n%s" % (subject, messageText)
        headers, message = newDecapitate(messageText)
        if mto: headers['to'] = mto
        if mfrom: headers['from'] = mfrom
        for requiredHeader in ('to', 'from', 'subject'):
            if not headers.has_key(requiredHeader):
                raise MailHostError,"Message missing SMTP Header '%s'"\
                % requiredHeader
    
        SendMail(self.smtpHost, self.smtpPort, self.localHost).send( 
                            mfrom=headers['from'], mto=headers['to'],
                            subj=headers['subject'], body=messageText)

    def scheduledSend(self, messageText, mto=None, mfrom=None, subject=None):
	if subject: messageText="subject: %s\n%s" % (subject, messageText)
	headers, message = newDecapitate(messageText)
	if mto: headers['to'] = mto
	if mfrom: headers['from'] = mfrom
	for requiredHeader in ('to', 'from', 'subject'):
	    if not headers.has_key(requiredHeader):
		raise MailHostError,"Message missing SMTP Header '%s'"\
		      % requiredHeader
    
	Globals.Scheduler.schedule(OneTimeEvent(
	    Send,
	    (self.smtpHost, self.smtpPort, self.localHost,
	     headers['from'], headers['to'],
	     headers['subject'], messageText
	     ),
	    threadsafe=1
	    ))

    def simple_send(self, mto, mfrom, subject, body):
        body="subject: %s\n\n%s" % (subject, body)
        SendMail(self.smtpHost, self.smtpPort, self.localHost).send( 
                        mfrom=mfrom, mto=mto, subj=subject, body=body)

class MailHost(Persistent, MailBase):
    "persistent version"

def Send(host, port, localhost, from_, to, subject, body):
    SendMail(host, port, localhost).send(from_, to, subject, body)
        
class SendMail:     
    def __init__(self, smtpHost, smtpPort, localHost="localhost"):
        self.conn = socket(AF_INET, SOCK_STREAM)
        self.conn.connect(smtpHost, smtpPort)
	self.fd=self.conn.fileno()
        self.conn.send("helo "+localHost+"\r\n")
	while 1:
	    if not self._check(): break

    def __del__(self):
        self._close()

    def getLine(self):
	line=''
	while 1:
	    if not select([self.fd],[],[],1.0)[0]:	#check the socket
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

    def send(self, mfrom, mto, subj, body):
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

def newDecapitate(message):
    blank_re =regex.compile('^[%s]+$' % string.whitespace)
    header_re=regex.symcomp('^\(<headerName>[^\0- <>:]+\):\(<headerText>.*\)$')
    space_re =regex.compile('^[%s]+' % string.whitespace)
    
    linecount=0; headerDict={};curHeader={}
    maxwell=map(lambda x: string.rstrip(x),string.split(message,'\n'))

    for line in maxwell:
        if not line: break
        if blank_re.match(line) >= 0: break
        if header_re.match(line) >=0:
            curHeader=string.lower(header_re.group('headerName'))
            headerDict[curHeader] =\
                        string.strip(header_re.group('headerText'))
        elif space_re.match(line)>=0:
            headerDict[curHeader] = "%s %s" % (headerDict[curHeader], line)
        linecount=linecount+1

    if headerDict.has_key('to'):
        headerDict['to']=map(
            lambda x: string.strip(x),
            string.split(headerDict['to'], ',')
            )
    
    body=string.join(maxwell[linecount:],'\n')
    return headerDict, body

def decapitate(message, **kw):
    #left behind for bw-compatibility
    return newDecapitate(message)




	
####################################################################
#
#$Log: MailHost.py,v $
#Revision 1.24  1998/01/05 19:34:12  jeffrey
#split out the SendMail tag machinery into new module
#
#Revision 1.23  1998/01/02 22:55:44  jeffrey
#minor cleanups, added SendMailTag class for DTML.
#
#Revision 1.22  1997/12/31 21:15:19  brian
#Security update
#
#Revision 1.21  1997/12/19 21:46:37  jeffrey
#fixees
#
#Revision 1.20  1997/12/18 16:45:37  jeffrey
#changeover to new ImageFile and HTMLFile handling
#
#Revision 1.19  1997/12/12 22:05:18  brian
#ui update
#
#Revision 1.18  1997/12/05 17:11:58  brian
#New UI
#
#Revision 1.17  1997/09/25 13:29:13  brian
#Removed index_html
#
#Revision 1.16  1997/09/18 20:08:51  brian
#Added meta_type for auto-detection
#
#Revision 1.15  1997/09/17 21:08:15  jeffrey
#threadsafe calls to Scheduler, added .scheduledSend method which is
#the same interface as send, but uses the schedular to send message
#instead of calling the SendMail class directly.
#
#Revision 1.14  1997/09/17 16:20:48  jim
#Added use of scheduler.
#
#Revision 1.13  1997/09/17 15:40:09  jeffrey
#Further SMTP and socket improvements
#
#Revision 1.12  1997/09/16 18:15:17  jeffrey
#Further SMTP updates...
#
#Revision 1.11  1997/09/16 16:59:01  jeffrey
#New SMTP checking..?
#
#Revision 1.10  1997/09/16 15:51:46  jeffrey
#(Hopefully) fixed some socket problems
#
#Revision 1.9  1997/09/12 15:00:00  jeffrey
#Finally added full support for RoleManager, also use of MessageDialog
#in the management process.
#
#Revision 1.8  1997/09/11 21:32:54  jeffrey
#sniffs out the 'local host' (web server host name thingy computer)
#
#Revision 1.6  1997/09/10 21:57:56  jeffrey
#Fixed nasty little squeeks, especially in:
# - header handling (now handles multi-line again)
# - an minor typo in the __del__ action for SendMail
#   (the class that actually communicates the SMTP)
#
#Revision 1.5  1997/09/10 18:41:19  jeffrey
#The grand "Should Be Working" version...
##
