## This script requires:
## - python >= 2.4
## - Zope 3's zope.testbrowser package:
##   http://www.zope.org/Members/benji_york/ZopeTestbrowser-0.9.0.tgz
##
## The just run:
## $python generate_conflicts.py
import base64
import string
import threading
import urllib2

from zope.testbrowser.browser import Browser

# create our browser
class AuthBrowser(Browser):

    def addBasicAuth(self,username,password):        
        self.addHeader(
            'Authorization',
            'Basic '+base64.encodestring(username+':'+password).strip()
            )

    def open(self,uri,include_server=True):
        if include_server:
            uri = server+uri
        return Browser.open(self,uri)

browser = AuthBrowser()

# constants
server = 'http://localhost:8080'
# the following user must be able to view the management screens
# and create file objects
username = 'username'
password = 'password'
browser.addBasicAuth(username,password)
threads = 10
filename = 'conflict.txt'
filesize = 10000
hits = 5

# delete the file if it's already there
browser.open('/manage_main')
if filename in [c.optionValue
                for c in browser.getControl(name='ids:list').controls]:
    browser.open('/manage_delObjects?ids:list='+filename)

# create it
browser.open('/manage_addFile?id='+filename)

# edit it, hopefully causing conflicts
data = 'X'*filesize
class EditThread(threading.Thread):

    def __init__(self,i):
        self.conflicts = 0
        self.browser = AuthBrowser()
        self.browser.handleErrors = False
        self.browser.addBasicAuth(username,password)
        threading.Thread.__init__(self,name=str(i))
        
    def run(self):
        for i in range(1,hits+1):            
            self.browser.open('/conflict.txt/manage_main')
            self.browser.getControl(name='title').value='Test Title'
            self.browser.getControl(name='filedata:text').value = data
            try:
                self.browser.getControl(name='manage_edit:method').click()
            except urllib2.HTTPError,e:
                # print e.read()
                self.conflicts += 1
                print "Thread %s - CONFLICT" % self.getName()
            else:
                print "Thread %s - EDIT" % self.getName()

thread_objects = []
for i in range(1,threads+1):
    t = EditThread(i)
    thread_objects.append(t)
    t.start()
for t in thread_objects:
    t.join()
total = 0
print
for t in thread_objects:
    print "Thread %s - %i conflicts seen" % (t.getName(),t.conflicts)
    total += t.conflicts
print
print "%i conflicts seen by browsers" % total

