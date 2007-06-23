############################################################################
# 
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
############################################################################

__version__='$Revision: 1.20 $'[11:-2]
import Globals
from Persistence import Persistent
from persistent import TimeStamp
from Acquisition import Implicit, aq_base, aq_parent, aq_inner
from AccessControl.Owned import Owned
from AccessControl.Role import RoleManager
from App.Management import Tabs
from OFS.SimpleItem import Item
from OFS.ObjectManager import UNIQUE
from AccessControl import ClassSecurityInfo
import SessionInterfaces
from SessionPermissions import *
from common import DEBUG
import os, time, random, string, binascii, sys, re
from cgi import escape
from urllib import quote
from urlparse import urlparse, urlunparse
from ZPublisher.BeforeTraverse import registerBeforeTraverse, \
    unregisterBeforeTraverse, queryBeforeTraverse
import logging

b64_trans = string.maketrans('+/', '-.')
b64_untrans = string.maketrans('-.', '+/')

badidnamecharsin = re.compile('[\?&;,<> ]').search
badcookiecharsin = re.compile('[;,<>& ]').search
twodotsin = re.compile('(\w*\.){2,}').search

_marker = []

constructBrowserIdManagerForm = Globals.DTMLFile('dtml/addIdManager',globals())

BROWSERID_MANAGER_NAME = 'browser_id_manager'# imported by SessionDataManager
ALLOWED_BID_NAMESPACES = ('form', 'cookies', 'url')
ADD_BROWSER_ID_MANAGER_PERM="Add Browser Id Manager"
TRAVERSAL_APPHANDLE = 'BrowserIdManager'

LOG = logging.getLogger('Zope.BrowserIdManager')

def constructBrowserIdManager(
    self, id=BROWSERID_MANAGER_NAME, title='', idname='_ZopeId',
    location=('cookies', 'form'), cookiepath='/', cookiedomain='',
    cookielifedays=0, cookiesecure=0, auto_url_encoding=0, REQUEST=None
    ):
    """ """
    ob = BrowserIdManager(id, title, idname, location, cookiepath,
                          cookiedomain, cookielifedays, cookiesecure,
                          auto_url_encoding)
    self._setObject(id, ob)
    ob = self._getOb(id)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)
    
class BrowserIdManagerErr(Exception): pass
    
class BrowserIdManager(Item, Persistent, Implicit, RoleManager, Owned, Tabs):
    """ browser id management class """

    meta_type = 'Browser Id Manager'

    manage_options=(
        {'label': 'Settings',
         'action':'manage_browseridmgr',
         },
        {'label': 'Security', 'action':'manage_access'},
        {'label': 'Ownership', 'action':'manage_owner'}
        )

    __implements__ = (SessionInterfaces.BrowserIdManagerInterface, )

    icon = 'misc_/Sessions/idmgr.gif'

    security = ClassSecurityInfo()
    security.declareObjectPublic()
    ok = {'meta_type':1, 'id':1, 'title': 1, 'icon':1,
          'bobobase_modification_time':1, 'title_or_id':1 }
    security.setDefaultAccess(ok)
    security.setPermissionDefault(MGMT_SCREEN_PERM, ['Manager'])
    security.setPermissionDefault(ACCESS_CONTENTS_PERM,['Manager','Anonymous'])
    security.setPermissionDefault(CHANGE_IDMGR_PERM, ['Manager'])

    # backwards-compatibility for pre-2.6 instances
    auto_url_encoding = 0

    def __init__(self, id, title='', idname='_ZopeId',
                 location=('cookies', 'form'), cookiepath=('/'),
                 cookiedomain='', cookielifedays=0, cookiesecure=0,
                 auto_url_encoding=0):
        self.id = str(id)
        self.title = str(title)
        self.setBrowserIdName(idname)
        self.setBrowserIdNamespaces(location)
        self.setCookiePath(cookiepath)
        self.setCookieDomain(cookiedomain)
        self.setCookieLifeDays(cookielifedays)
        self.setCookieSecure(cookiesecure)
        self.setAutoUrlEncoding(auto_url_encoding)

    def manage_afterAdd(self, item, container):
        """ Maybe add our traversal hook """
        self.updateTraversalData()

    def manage_beforeDelete(self, item, container):
        """ Remove our traversal hook if it exists """
        self.unregisterTraversalHook()

    security.declareProtected(ACCESS_CONTENTS_PERM, 'hasBrowserId')
    def hasBrowserId(self):
        """ Returns true if there is a current browser id, but does
        not create a browser id for the current request if one doesn't
        already exist """
        if self.getBrowserId(create=0): return 1
                
    security.declareProtected(ACCESS_CONTENTS_PERM, 'getBrowserId')
    def getBrowserId(self, create=1):
        """
        Examines the request and hands back browser id value or
        None if no id exists.  If there is no browser id
        and if 'create' is true, create one.  If cookies are are
        an allowable id namespace and create is true, set one.  Stuff
        the id and the namespace it was found in into the REQUEST object
        for further reference during this request.
        """
        REQUEST = self.REQUEST
        # let's see if bid has already been attached to request
        bid = getattr(REQUEST, 'browser_id_', None)
        if bid is not None:
            # it's already set in this request so we can just return it
            # if it's well-formed
            if not isAWellFormedBrowserId(bid):
                # somebody screwed with the REQUEST instance during
                # this request.
                raise BrowserIdManagerErr, (
                    'Ill-formed browserid in REQUEST.browser_id_:  %s' % 
                    escape(bid)
                    )
            return bid
        # fall through & ck form/cookie namespaces if bid is not in request.
        tk = self.browserid_name
        ns = self.browserid_namespaces
        for name in ns:
            if name == 'url':
                continue # browser ids in url are checked by Traverser class
            current_ns = getattr(REQUEST, name, None)
            if current_ns is None:
                continue
            bid = current_ns.get(tk, None)
            if bid is not None:
                # hey, we got a browser id!
                if isAWellFormedBrowserId(bid):
                    # bid is not "plain old broken"
                    REQUEST.browser_id_ = bid
                    REQUEST.browser_id_ns_ = name
                    return bid
        # fall through if bid is invalid or not in namespaces
        if create:
            # create a brand new bid
            bid = getNewBrowserId()
            if 'cookies' in ns:
                self._setCookie(bid, REQUEST)
            REQUEST.browser_id_ = bid
            REQUEST.browser_id_ns_ = None
            return bid
        # implies a return of None if:
        # (not create=1) and (invalid or ((not in req) and (not in ns)))

    security.declareProtected(ACCESS_CONTENTS_PERM, 'flushBrowserIdCookie')
    def flushBrowserIdCookie(self):
        """ removes the bid cookie from the client browser """
        if 'cookies' not in self.browserid_namespaces:
            raise BrowserIdManagerErr,('Cookies are not now being used as a '
                                       'browser id namespace, thus the '
                                       'browserid cookie cannot be flushed.')
        self._setCookie('deleted', self.REQUEST, remove=1)

    security.declareProtected(ACCESS_CONTENTS_PERM,'setBrowserIdCookieByForce')
    def setBrowserIdCookieByForce(self, bid):
        """ """
        if 'cookies' not in self.browserid_namespaces:
            raise BrowserIdManagerErr,('Cookies are not now being used as a '
                                       'browser id namespace, thus the '
                                       'browserid cookie cannot be forced.')
        self._setCookie(bid, self.REQUEST)

    security.declareProtected(ACCESS_CONTENTS_PERM, 'isBrowserIdFromCookie')
    def isBrowserIdFromCookie(self):
        """ returns true if browser id is from REQUEST.cookies """
        if not self.getBrowserId(): # make sure the bid is stuck on REQUEST
            raise BrowserIdManagerErr, 'There is no current browser id.'
        if getattr(self.REQUEST, 'browser_id_ns_') == 'cookies':
            return 1

    security.declareProtected(ACCESS_CONTENTS_PERM, 'isBrowserIdFromForm')
    def isBrowserIdFromForm(self):
        """ returns true if browser id is from REQUEST.form """
        if not self.getBrowserId(): # make sure the bid is stuck on REQUEST
            raise BrowserIdManagerErr, 'There is no current browser id.'
        if getattr(self.REQUEST, 'browser_id_ns_') == 'form':
            return 1

    security.declareProtected(ACCESS_CONTENTS_PERM, 'isBrowserIdFromUrl')
    def isBrowserIdFromUrl(self):
        """ returns true if browser id is from first element of the
        URL """
        if not self.getBrowserId(): # make sure the bid is stuck on REQUEST
            raise BrowserIdManagerErr, 'There is no current browser id.'
        if getattr(self.REQUEST, 'browser_id_ns_') == 'url':
            return 1

    security.declareProtected(ACCESS_CONTENTS_PERM, 'isBrowserIdNew')
    def isBrowserIdNew(self):
        """
        returns true if browser id is 'new', meaning the id exists
        but it has not yet been acknowledged by the client (the client
        hasn't sent it back to us in a cookie or in a formvar).
        """
        if not self.getBrowserId(): # make sure the id is stuck on REQUEST
            raise BrowserIdManagerErr, 'There is no current browser id.'
        # ns will be None if new, negating None below returns 1, which
        # would indicate that it's new on this request
        return getattr(self.REQUEST, 'browser_id_ns_', None) == None
    
    security.declareProtected(ACCESS_CONTENTS_PERM, 'encodeUrl')
    def encodeUrl(self, url, style='querystring', create=1):
        """
        encode a URL with the browser id as a postfixed query string
        element or inlined into the url depending on the 'style' parameter
        """
        bid = self.getBrowserId(create)
        if bid is None:
            raise BrowserIdManagerErr, 'There is no current browser id.'
        name = self.getBrowserIdName()
        if style == 'querystring': # encode bid in querystring
            if '?' in url:
                return '%s&amp;%s=%s' % (url, name, bid)
            else:
                return '%s?%s=%s' % (url, name, bid)
        else: # encode bid as first two URL path segments
            proto, host, path, params, query, frag = urlparse(url)
            path = '/%s/%s%s' % (name, bid, path)
            return urlunparse((proto, host, path, params, query, frag))

    security.declareProtected(MGMT_SCREEN_PERM, 'manage_browseridmgr')
    manage_browseridmgr = Globals.DTMLFile('dtml/manageIdManager', globals())

    security.declareProtected(CHANGE_IDMGR_PERM,
                              'manage_changeBrowserIdManager')
    def manage_changeBrowserIdManager(
        self, title='', idname='_ZopeId', location=('cookies', 'form'),
        cookiepath='/', cookiedomain='', cookielifedays=0, cookiesecure=0,
        auto_url_encoding=0, REQUEST=None
        ):
        """ """
        self.title = str(title)
        self.setBrowserIdName(idname)
        self.setCookiePath(cookiepath)
        self.setCookieDomain(cookiedomain)
        self.setCookieLifeDays(cookielifedays)
        self.setCookieSecure(cookiesecure)
        self.setBrowserIdNamespaces(location)
        self.setAutoUrlEncoding(auto_url_encoding)
        self.updateTraversalData()
        if REQUEST is not None:
            msg = '/manage_browseridmgr?manage_tabs_message=Changes saved'
            REQUEST.RESPONSE.redirect(self.absolute_url()+msg)

    security.declareProtected(CHANGE_IDMGR_PERM, 'setBrowserIdName')
    def setBrowserIdName(self, k):
        """ sets browser id name string """
        if not (type(k) is type('') and k and not badidnamecharsin(k)):
            raise BrowserIdManagerErr,'Bad id name string %s' % escape(repr(k))
        self.browserid_name = k

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getBrowserIdName')
    def getBrowserIdName(self):
        """ """
        return self.browserid_name

    security.declareProtected(CHANGE_IDMGR_PERM, 'setBrowserIdNamespaces')
    def setBrowserIdNamespaces(self, ns):
        """
        accepts list of allowable browser id namespaces 
        """
        for name in ns:
            if name not in ALLOWED_BID_NAMESPACES:
                raise BrowserIdManagerErr, (
                    'Bad browser id namespace %s' % repr(name)
                    )
        self.browserid_namespaces = tuple(ns)

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getBrowserIdNamespaces')
    def getBrowserIdNamespaces(self):
        """ """
        return self.browserid_namespaces

    security.declareProtected(CHANGE_IDMGR_PERM, 'setCookiePath')
    def setCookiePath(self, path=''):
        """ sets cookie 'path' element for id cookie """
        if not (type(path) is type('') and not badcookiecharsin(path)):
            raise BrowserIdManagerErr,'Bad cookie path %s' % escape(repr(path))
        self.cookie_path = path
    
    security.declareProtected(ACCESS_CONTENTS_PERM, 'getCookiePath')
    def getCookiePath(self):
        """ """
        return self.cookie_path

    security.declareProtected(CHANGE_IDMGR_PERM, 'setCookieLifeDays')
    def setCookieLifeDays(self, days):
        """ offset for id cookie 'expires' element """
        if type(days) not in (type(1), type(1.0)):
            raise BrowserIdManagerErr,(
                'Bad cookie lifetime in days %s (requires integer value)'
                % escape(repr(days))
                )
        self.cookie_life_days = int(days)

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getCookieLifeDays')
    def getCookieLifeDays(self):
        """ """
        return self.cookie_life_days

    security.declareProtected(CHANGE_IDMGR_PERM, 'setCookieDomain')
    def setCookieDomain(self, domain):
        """ sets cookie 'domain' element for id cookie """
        if type(domain) is not type(''):
            raise BrowserIdManagerErr, (
                'Cookie domain must be string: %s' % escape(repr(domain))
                )
        if not domain:
            self.cookie_domain = ''
            return
        if not twodotsin(domain):
            raise BrowserIdManagerErr, (
                'Cookie domain must contain at least two dots (e.g. '
                '".zope.org" or "www.zope.org") or it must be left blank. : '
                '%s' % escape(`domain`)
                )
        if badcookiecharsin(domain):
            raise BrowserIdManagerErr, (
                'Bad characters in cookie domain %s' % escape(`domain`)
                )
        self.cookie_domain = domain

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getCookieDomain')
    def getCookieDomain(self):
        """ """
        return self.cookie_domain

    security.declareProtected(CHANGE_IDMGR_PERM, 'setCookieSecure')
    def setCookieSecure(self, secure):
        """ sets cookie 'secure' element for id cookie """
        self.cookie_secure = not not secure

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getCookieSecure')
    def getCookieSecure(self):
        """ """
        return self.cookie_secure

    security.declareProtected(CHANGE_IDMGR_PERM, 'setCookieSecure')
    def setAutoUrlEncoding(self, auto_url_encoding):
        """ sets 'auto url encoding' on or off """
        self.auto_url_encoding = not not auto_url_encoding

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getAutoUrlEncoding')
    def getAutoUrlEncoding(self):
        """ """
        return self.auto_url_encoding

    security.declareProtected(ACCESS_CONTENTS_PERM, 'isUrlInBidNamespaces')
    def isUrlInBidNamespaces(self):
        """ Returns true if 'url' is in the browser id namespaces
        for this browser id """
        return 'url' in self.browserid_namespaces

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getHiddenFormField')
    def getHiddenFormField(self):
        """
        Convenience method which returns a hidden form element
        representing the current browser id name and browser id
        """
        s = '<input type="hidden" name="%s" value="%s">'
        return s % (self.getBrowserIdName(), self.getBrowserId())

    def _setCookie(
        self, bid, REQUEST, remove=0, now=time.time, strftime=time.strftime,
        gmtime=time.gmtime
        ):
        """ """
        expires = None
        if remove:
            expires = "Sun, 10-May-1971 11:59:00 GMT"
        elif self.cookie_life_days:
            expires = now() + self.cookie_life_days * 86400
            # Wdy, DD-Mon-YYYY HH:MM:SS GMT
            expires = strftime('%a %d-%b-%Y %H:%M:%S GMT',gmtime(expires))
        d = {'domain':self.cookie_domain,'path':self.cookie_path,
             'secure':self.cookie_secure,'expires':expires}

        if self.cookie_secure:
            URL1 = REQUEST.get('URL1', None)
            if URL1 is None:
                return # should we raise an exception?
            if string.split(URL1,':')[0] != 'https':
                return # should we raise an exception?
         
        cookies = REQUEST.RESPONSE.cookies
        cookie = cookies[self.browserid_name]= {}
        for k,v in d.items():
            if v:
                cookie[k] = v #only stuff things with true values
        cookie['value'] = bid
        
    def _setId(self, id):
        if id != self.id:
            raise Globals.MessageDialog(
                title='Cannot rename',
                message='You cannot rename a browser id manager, sorry!',
                action ='./manage_main',)

    def updateTraversalData(self):
        if self.isUrlInBidNamespaces():
            self.registerTraversalHook()
        else:
            self.unregisterTraversalHook()

    def unregisterTraversalHook(self):
        parent = aq_parent(aq_inner(self))
        name = TRAVERSAL_APPHANDLE
        if self.hasTraversalHook(parent):
            unregisterBeforeTraverse(parent, name)

    def registerTraversalHook(self):
        parent = aq_parent(aq_inner(self))
        if not self.hasTraversalHook(parent):
            hook = BrowserIdManagerTraverser()
            name = TRAVERSAL_APPHANDLE
            priority = 40 # "higher" priority than session data traverser
            registerBeforeTraverse(parent, hook, name, priority)

    def hasTraversalHook(self, parent):
        name = TRAVERSAL_APPHANDLE
        return not not queryBeforeTraverse(parent, name)
                       
class BrowserIdManagerTraverser(Persistent):
    def __call__(self, container, request, browser_id=None,
                 browser_id_ns=None,
                 BROWSERID_MANAGER_NAME=BROWSERID_MANAGER_NAME):
        """
        Registered hook to set and get a browser id in the URL.  If
        a browser id is found in the URL of an  incoming request, we put it
        into a place where it can be found later by the browser id manager.
        If our browser id manager's auto-url-encoding feature is on, cause
        Zope-generated URLs to contain the browser id by rewriting the
        request._script list.
        """
        browser_id_manager = getattr(container, BROWSERID_MANAGER_NAME, None)
        # fail if we cannot find a browser id manager (that means this
        # instance has been "orphaned" somehow)
        if browser_id_manager is None:
            LOG.error('Could not locate browser id manager!')
            return

        try:
            stack = request['TraversalRequestNameStack']
            request.browser_id_ns_ = browser_id_ns
            bid_name = browser_id_manager.getBrowserIdName()

            # stuff the browser id and id namespace into the request
            # if the URL has a browser id name and browser id as its first
            # two elements.  Only remove these elements from the
            # traversal stack if they are a "well-formed pair".
            if len(stack) >= 2 and stack[-1] == bid_name:
                if isAWellFormedBrowserId(stack[-2]):
                    name       = stack.pop() # pop the name off the stack
                    browser_id = stack.pop() # pop id off the stack
                    request.browser_id_    = browser_id
                    request.browser_id_ns_ = 'url'

            # if the browser id manager is set up with 'auto url encoding',
            # cause generated URLs to be encoded with the browser id name/value
            # pair by munging request._script.
            if browser_id_manager.getAutoUrlEncoding():
                if browser_id is None:
                    request.browser_id_ = browser_id = getNewBrowserId()
                request._script.append(quote(bid_name))
                request._script.append(quote(browser_id))
        except:
            LOG.error('indeterminate error', exc_info=sys.exc_info())

def getB64TStamp(
    b2a=binascii.b2a_base64,gmtime=time.gmtime, time=time.time,
    b64_trans=b64_trans, split=string.split,
    TimeStamp=TimeStamp.TimeStamp, translate=string.translate
    ):
    t=time()
    ts=split(b2a(`TimeStamp(*gmtime(t)[:5]+(t%60,))`)[:-1],'=')[0]
    return translate(ts, b64_trans)

def getB64TStampToInt(
    ts, TimeStamp=TimeStamp.TimeStamp, b64_untrans=b64_untrans,
    a2b=binascii.a2b_base64, translate=string.translate
    ):
    return TimeStamp(a2b(translate(ts+'=',b64_untrans))).timeTime()

def getBrowserIdPieces(bid):
    """ returns browser id parts in a tuple consisting of rand_id,
    timestamp
    """
    return (bid[:8], bid[8:19])


def isAWellFormedBrowserId(bid, binerr=binascii.Error):
    try:
        rnd, ts = getBrowserIdPieces(bid)
        int(rnd)
        getB64TStampToInt(ts)
        return bid
    except (TypeError, ValueError, AttributeError, IndexError, binerr):
        return None


def getNewBrowserId(randint=random.randint, maxint=99999999):
    """ Returns 19-character string browser id
    'AAAAAAAABBBBBBBB'
    where:

    A == leading-0-padded 8-char string-rep'd random integer
    B == modified base64-encoded 11-char timestamp

    To be URL-compatible, base64 encoding is modified as follows:
      '=' end-padding is stripped off
      '+' is translated to '-'
      '/' is translated to '.'

    An example is: 89972317A0C3EHnUi90w
    """
    return '%08i%s' % (randint(0, maxint-1), getB64TStamp())


Globals.InitializeClass(BrowserIdManager)
