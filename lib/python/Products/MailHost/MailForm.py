from Globals import Persistent, HTMLFile, HTML
from socket import *
import Acquisition, sys, regex, string

smtpError = "SMTP Error"

addForm=HTMLFile('MailForm/addMailForm_form')
def add(self, id='mailForm', title='Some mail thing', smtp_host=None, 
		localhost='localhost', smtp_port=25, mailTemplate=None,
		errorTemplate=None, sentMailTemplate=None, REQUEST):
	' add a MailForm into the system '
	i=MailForm()			#create new mailform
	i.id=id					#give it id
	i.title=title			#title
	i._init(localHost=localhost, smtpHost=smtp_host, smtpPort=smtp_port,
			mailTemplate=mailTemplate, errorTemplate=errorTemplate,
			sentMailTemplate=sentMailTemplate)
	self._setObject(id,i)	#register it
	return self.manage_main(self,REQUEST)	#and whatever this does..  :)


class MailForm(Persistent, Acquisition.Implicit):
	'a mailform...?'
	manage=HTMLFile('MailForm/manageMailForm')
	
	index_html=HTMLFile('MailForm/manageMailForm')
	
	def __init__(self):
		'nothing yet'
		pass

	def _init(self,localHost, smtpHost, smtpPort, mailTemplate, errorTemplate,
			  sentMailTemplate):
		self.localHost=localHost
		self.smtpHost=smtpHost
		self.smtpPort=smtpPort
		self.mailTemplate=mailTemplate
		self.errorTemplate=errorTemplate
		self.sentMailTemplate=sentMailTemplate

	def manage_makeChanges(self, title, localHost, smtpHost, smtpPort):
		'make the changes'
		self.title=title
		self.localHost=localHost
		self.smtpHost=smtpHost
		self.smtpPort=smtpPort
		return ('Changes made','Changes made...')
		
	def send(trueself, self):
		'uhh, sponges off the request and mails it..?'
		messageText=getattr(self,self.mailTemplate)(self, trueself.REQUEST)
		headers, message=decapitate(messageText)
		for requiredHeader in ('to', 'from', 'subject'):
			if not headers.has_key(requiredHeader):
				raise MailFormError, "Message missing SMTP Header '%s'" \
				% requiredHeader
		trueself._mailConnect()
		trueself._send(mfrom=headers['from'], mto=headers['to'], 
					   subj=headers['subject'], body=messageText)
		trueself._close()
		return getattr(self,self.sentMailTemplate)(self, self.REQUEST, 
												messageText=message)
		
	def _mailConnect(self):
		self._v_conn = socket(AF_INET, SOCK_STREAM)
		self._v_conn.connect(self.smtpHost, self.smtpPort)
		self._v_conn.send("helo "+self.localHost+"\r\n")
		self._check('220')

	def _check(self, lev='250'):
		data = self._v_conn.recv(1024)
		if data[:3] != lev:
			raise smtpError, "Expected %s, got %s from SMTP"%(lev, data[:3])

	def _send(self, mfrom, mto, subj, body):
		self._v_conn.send("mail from:<%s>\n"%mfrom)
		self._check()
		if type(mto) == type([1,2]):
			for person in mto:
				self._v_conn.send("rcpt to:<%s>\n" % person)
				self._check()
		else:
			self._v_conn.send("rcpt to:<%s>\n"%mto)
			self._check()
		self._v_conn.send("data\n")
		self._check()
		self._v_conn.send(body)
		self._v_conn.send("\n.\n")
		self._check('354')

	def _close(self):
		self._v_conn.send("quit\n")
		self._v_conn.close()

def decapitate(message,
			   header_re=regex.compile(
				   '\(\('
						  '[^\0- <>:]+:[^\n]*\n'
					  '\|'
						  '[ \t]+[^\0- ][^\n]*\n'
				   '\)+\)[ \t]*\n\([\0-\377]+\)'
				   ),
			   space_re=regex.compile('\([ \t]+\)'),
			   name_re=regex.compile('\([^\0- <>:]+\):\([^\n]*\)'),
			   ):
	if header_re.match(message) < 0: return message

	headers, body = header_re.group(1,3)

	headers=string.split(headers,'\n')
	headerDict={}

	i=1
	while i < len(headers):
		if not headers[i]:
			del headers[i]
		elif space_re.match(headers[i]) >= 0:
			headers[i-1]="%s %s" % (headers[i-1],
									headers[i][len(space_re.group(1)):])
			del headers[i]
		else:
			i=i+1

	for i in range(len(headers)):
		if name_re.match(headers[i]) >= 0:
			k, v = name_re.group(1,2)
			k=string.lower(k); v=string.strip(v)
			headerDict[k]=v
		else:
			raise ValueError, 'Invalid Header (%d): %s ' % (i,headers[i])

	if headerDict.has_key('to'):
		headerDict['to']=map(
			lambda x: string.strip(x),
			string.split(headerDict['to'], ',')
			)

	return headerDict, body
