from Globals import Persistent, HTMLFile, HTML, MessageDialog
from socket import *; from select import select
from AccessControl.Role import RoleManager
import Acquisition, sys, regex, string, types
import OFS.SimpleItem
import Globals
from Scheduler.OneTimeEvent import OneTimeEvent

#$Id: MailHost.py,v 1.14 1997/09/17 16:20:48 jim Exp $ 
__version__ = "$Revision: 1.14 $"[11:-2]
smtpError = "SMTP Error"
MailHostError = "MailHost Error"

addForm=HTMLFile('MailHost/addMailHost_form',localhost=gethostname())
def add(self, id='aMailHost', title='Some mail thing', smtp_host=None, 
        localhost='localhost', smtp_port=25, acl_type='A',acl_roles=[], 
        REQUEST=None):
    ' add a MailHost into the system '
    i=MailHost()            #create new mail host
    i.id=id                 #give it id
    i.title=title           #title
    i._init(localHost=localhost, smtpHost=smtp_host, smtpPort=smtp_port)
    i._setRoles(acl_type, acl_roles)
    self._setObject(id,i)   #register it
    return self.manage_main(self,REQUEST)   #and whatever this does.. :)


class MailHost(Persistent, Acquisition.Implicit, OFS.SimpleItem.Item,
               RoleManager):
    'a mailhost...?'
    manage=HTMLFile('MailHost/manageMailHost')
    index_html=HTMLFile('MailHost/mailHost')
    icon="MailHost/MailHost_icon.gif"
    
    def __init__(self):
        'nothing yet'
        pass

    def _init(self, localHost, smtpHost, smtpPort):
        self.localHost=localHost
        self.smtpHost=smtpHost
        self.smtpPort=smtpPort
        self.sentMessages=0

    def manage_makeChanges(self, title, localHost, smtpHost, smtpPort,
                          acl_type='A',acl_roles=[], REQUEST=None):
        'make the changes'
        self.title=title
        self.localHost=localHost
        self.smtpHost=smtpHost
        self.smtpPort=smtpPort
        self._setRoles(acl_type, acl_roles)
        return MessageDialog(
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
	     )
	    ))

	return "SEND OK"
        
    def send(self, messageText, mto=None, mfrom=None):
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

    def simple_send(self, mto, mfrom, subject, body):
        body="subject: %s\n\n%s" % (subject, body)
        SendMail(self.smtpHost, self.smtpPort, self.localHost).send( 
                        mfrom=mfrom, mto=mto, subj=subject, body=body)

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
	    if not select([self.fd],[],[],1.0)[0]:
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
            #raise smtpError, "Expected %s, got %s from SMTP" % (lev, data[:3])
	    raise smtpError, "Recieved error code %s from SMTP: %s"\
		  % (code, line)
	return 1

    def send(self, mfrom, mto, subj, body):
        self.conn.send("mail from:<%s>\n"%mfrom)
        self._check()
        if type(mto) in [types.ListType, types.TupleType]:
            for person in mto:
                self.conn.send("rcpt to:<%s>\n" % person)
                self._check()
        else:
            self.conn.send("rcpt to:<%s>\n"%mto)
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


#$Log: MailHost.py,v $
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
