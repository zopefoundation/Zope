from Globals import Persistent, HTMLFile, HTML
from socket import *
import Acquisition, sys, regex, string

smtpError = "SMTP Error"

addForm=HTMLFile('MailForm/addMailForm_form')
def add(self, id='mailForm', title='Some mail thing', smtp_host=None, 
        localhost='localhost', smtp_port=25, mailTemplate=None,
        errorTemplate=None, sentMailTemplate=None, REQUEST):
    ' add a MailForm into the system '
    i=MailForm()            #create new mailform
    i.id=id                 #give it id
    i.title=title           #title
    i._init(localHost=localhost, smtpHost=smtp_host, smtpPort=smtp_port,
            mailTemplate=mailTemplate, errorTemplate=errorTemplate,
            sentMailTemplate=sentMailTemplate)
    self._setObject(id,i)   #register it
    return self.manage_main(self,REQUEST)   #and whatever this does..  :)


class MailForm(Persistent, Acquisition.Implicit):
    'a mailform...?'
    manage=HTMLFile('MailForm/manageMailForm')
    index_html=HTMLFile('MailForm/mailForm')
    
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
        if trueself.REQUEST.has_key('d_template'):
            mtemplate = getattr(self, trueself.REQUEST['d_template'])
        else:
            mtemplate = getattr(self, trueself.mailTemplate)
        messageText = mtemplate(self, trueself.REQUEST)
        headers, message = decapitate(messageText)
        for requiredHeader in ('to', 'from', 'subject'):
            if not headers.has_key(requiredHeader):
                raise MailFormError, "Message missing SMTP Header '%s'" \
                % requiredHeader
        
        SendMail(self.smtpHost, self.smtpPort, self.localHost).send(
                        mfrom=headers['from'], mto=headers['to'], 
                        subj=headers['subject'], body=messageText)

        return getattr(self,self.sentMailTemplate)(self, self.REQUEST, 
                                                messageText=message)

    def trueSend(trueself, self=None, REQUEST=None, **kw):
        if REQUEST: kw=REQUEST
        if not self: self=trueself
        if kw.has_key('d_template'):
            mtemplate = getattr(self, kw['d_template'])
        else:
            mtemplate = getattr(self, trueself.mailTemplate)
        messageText = mtemplate(self, kw)
        headers, message = decapitate(messageText)
        for requiredHeader in ('to', 'from', 'subject'):
            if not headers.has_key(requiredHeader):
                raise MailFormError, "Message missing SMTP Header '%s'" \
                % requiredHeader
        
        SendMail(trueself.smtpHost, trueself.smtpPort, 
                 trueself.localHost).send( 
                        mfrom=headers['from'], mto=headers['to'],
                        subj=headers['subject'], body=messageText
                        )

        return getattr(trueself,trueself.sentMailTemplate)(self, kw, 
                                                messageText=message)

class SendMail:     
    def __init__(self, smtpHost, smtpPort, localHost="localhost"):
        self.conn = socket(AF_INET, SOCK_STREAM)
        self.conn.connect(smtpHost, smtpPort)
        self.conn.send("helo "+localHost+"\r\n")
        self._check('220')

    def __del__(self):
        self.close()

    def _check(self, lev='250'):
        data = self.conn.recv(1024)
        if data[:3] != lev:
            raise smtpError, "Expected %s, got %s from SMTP"%(lev, data[:3])

    def send(self, mfrom, mto, subj, body):
        self.conn.send("mail from:<%s>\n"%mfrom)
        self._check()
        if type(mto) == type([1,2]):
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
