############################################################################
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
############################################################################

__version__='$Revision: 1.13 $'[11:-2]
import Globals
from Persistence import Persistent
from ZODB import TimeStamp
from Acquisition import Implicit
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

b64_trans = string.maketrans('+/', '-.')
b64_untrans = string.maketrans('-.', '+/')

badidnamecharsin = re.compile('[\?&;,<> ]').search
badcookiecharsin = re.compile('[;,<>& ]').search
twodotsin = re.compile('(\w*\.){2,}').search

_marker = []

constructBrowserIdManagerForm = Globals.DTMLFile('dtml/addIdManager',globals())

ADD_BROWSER_ID_MANAGER_PERM="Add Browser Id Manager"

def constructBrowserIdManager(
    self, id, title='', idname='_ZopeId', location='cookiethenform',
    cookiepath='/', cookiedomain='', cookielifedays=0, cookiesecure=0,
    REQUEST=None
    ):
    """ """
    ob = BrowserIdManager(id, title, idname, location, cookiepath,
                          cookiedomain, cookielifedays, cookiesecure)
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
    ok = {'meta_type':1, 'id':1, 'title': 1, 'icon':1,
          'bobobase_modification_time':1 }
    security.setDefaultAccess(ok)
    security.setPermissionDefault(MGMT_SCREEN_PERM, ['Manager'])
    security.setPermissionDefault(ACCESS_CONTENTS_PERM,['Manager','Anonymous'])
    security.setPermissionDefault(CHANGE_IDMGR_PERM, ['Manager'])

    def __init__(self, id, title='', idname='_ZopeId',
                 location='cookiesthenform', cookiepath=('/'),
                 cookiedomain='', cookielifedays=0, cookiesecure=0):
        self.id = str(id)
        self.title = str(title)
        self.setBrowserIdName(idname)
        self.setBrowserIdLocation(location)
        self.setCookiePath(cookiepath)
        self.setCookieDomain(cookiedomain)
        self.setCookieLifeDays(cookielifedays)
        self.setCookieSecure(cookiesecure)

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
            if not self._isAWellFormedBrowserId(bid):
                # somebody screwed with the REQUEST instance during
                # this request.
                raise BrowserIdManagerErr, (
                    'Ill-formed browserid in REQUEST.browser_id_:  %s' % 
                    escape(bid)
                    )
            return bid
        # fall through & ck id namespaces if bid is not in request.
        tk = self.browserid_name
        ns = self.browserid_namespaces
        for name in ns:
            bid = getattr(REQUEST, name).get(tk, None)
            if bid is not None:
                # hey, we got a browser id!
                if self._isAWellFormedBrowserId(bid):
                    # bid is not "plain old broken"
                    REQUEST.browser_id_ = bid
                    REQUEST.browser_id_ns_ = name
                    return bid
        # fall through if bid is invalid or not in namespaces
        if create:
            # create a brand new bid
            bid = self._getNewBrowserId()
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
        return not getattr(self.REQUEST, 'browser_id_ns_')
    
    security.declareProtected(ACCESS_CONTENTS_PERM, 'encodeUrl')
    def encodeUrl(self, url, create=1):
        """
        encode a URL with the browser id as a postfixed query string
        element
        """
        bid = self.getBrowserId(create)
        if bid is None:
            raise BrowserIdManagerErr, 'There is no current browser id.'
        name = self.getBrowserIdName()
        if '?' in url:
            return '%s&amp;%s=%s' % (url, name, bid)
        else:
            return '%s?%s=%s' % (url, name, bid)

    security.declareProtected(MGMT_SCREEN_PERM, 'manage_browseridmgr')
    manage_browseridmgr = Globals.DTMLFile('dtml/manageIdManager', globals())

    security.declareProtected(CHANGE_IDMGR_PERM,
                              'manage_changeBrowserIdManager')
    def manage_changeBrowserIdManager(
        self, title='', idname='_ZopeId', location='cookiesthenform',
        cookiepath='/', cookiedomain='', cookielifedays=0, cookiesecure=0,
        REQUEST=None
        ):
        """ """
        self.title = title
        self.setBrowserIdName(idname)
        self.setCookiePath(cookiepath)
        self.setCookieDomain(cookiedomain)
        self.setCookieLifeDays(cookielifedays)
        self.setCookieSecure(cookiesecure)
        self.setBrowserIdLocation(location)
        if REQUEST is not None:
            return self.manage_browseridmgr(
                self, REQUEST, manage_tabs_message = 'Changes saved.'
                )

    security.declareProtected(CHANGE_IDMGR_PERM, 'setBrowserIdName')
    def setBrowserIdName(self, k):
        """ sets browser id name string """
        if not (type(k) is type('') and k and not badidnamecharsin(k)):
            raise BrowserIdManagerErr, 'Bad id name string %s' % escape(repr(k))
        self.browserid_name = k

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getBrowserIdName')
    def getBrowserIdName(self):
        """ """
        return self.browserid_name

    security.declareProtected(CHANGE_IDMGR_PERM, 'setBrowserIdNamespaces')
    def setBrowserIdNamespaces(self,namespacesd={1:'cookies',2:'form'}):
        """
        accepts dictionary e.g. {1: 'cookies', 2: 'form'} as browser
        id allowable namespaces and lookup ordering priority
        where key is 'priority' with 1 being highest.
        """
        allowed = self.getAllBrowserIdNamespaces()
        for name in namespacesd.values():
            if name not in allowed:
                raise BrowserIdManagerErr, (
                    'Bad browser id namespace %s' % repr(name)
                    )
        self.browserid_namespaces = []
        nskeys = namespacesd.keys()
        nskeys.sort()
        for priority in nskeys:
            self.browserid_namespaces.append(namespacesd[priority])

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getBrowserIdLocation')
    def getBrowserIdLocation(self):
        d = {}
        i = 1
        for name in self.browserid_namespaces:
            d[name] = i
            i = i + 1
        if d.get('cookies') == 1:
            if d.get('form'):
                return 'cookiesthenform'
            else:
                return 'cookiesonly'
        elif d.get('form') == 1:
            if d.get('cookies'):
                return 'formthencookies'
            else:
                return 'formonly'
        else:
            return 'cookiesthenform'

    security.declareProtected(CHANGE_IDMGR_PERM, 'setBrowserIdLocation')
    def setBrowserIdLocation(self, location):
        """ accepts a string and turns it into a namespaces dict """
        if location == 'formthencookies':
            d = {1:'form', '2':'cookies'}
        elif location == 'cookiesonly':
            d = {1:'cookies'}
        elif location == 'formonly':
            d = {1:'form'}
        else:
            d = {1:'cookies',2:'form'}
        self.setBrowserIdNamespaces(d)

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getBrowserIdNamespaces')
    def getBrowserIdNamespaces(self):
        """ """
        d = {}
        i = 1
        for name in self.browserid_namespaces:
            d[i] = name
            i = i + 1
        return d

    security.declareProtected(CHANGE_IDMGR_PERM, 'setCookiePath')
    def setCookiePath(self, path=''):
        """ sets cookie 'path' element for id cookie """
        if not (type(path) is type('') and not badcookiecharsin(path)):
            raise BrowserIdManagerErr, 'Bad cookie path %s' % escape(repr(path))
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

    security.declareProtected(ACCESS_CONTENTS_PERM,'getAllBrowserIdNamespaces')
    def getAllBrowserIdNamespaces(self):
        """
        These are the REQUEST namespaces searched when looking for an
        browser id.
        """
        return ('form', 'cookies')

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getHiddenFormField')
    def getHiddenFormField(self):
        """
        Convenience method which returns a hidden form element
        representing the current browser id name and browser id
        """
        s = '<input type="hidden" name="%s" value="%s">'
        return s % (self.getBrowserIdName(), self.getBrowserId())

    # non-interface methods follow

    def _getNewBrowserId(self, randint=random.randint, maxint=99999999):
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
        return '%08i%s' % (randint(0, maxint-1), self._getB64TStamp())

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
        
    def _getB64TStamp(
        self, b2a=binascii.b2a_base64,gmtime=time.gmtime, time=time.time,
        b64_trans=b64_trans, split=string.split,
        TimeStamp=TimeStamp.TimeStamp, translate=string.translate
        ):
        t=time()
        ts=split(b2a(`apply(TimeStamp,(gmtime(t)[:5]+(t%60,)))`)[:-1],'=')[0]
        return translate(ts, b64_trans)

    def _getB64TStampToInt(
        self, ts, TimeStamp=TimeStamp.TimeStamp, b64_untrans=b64_untrans,
        a2b=binascii.a2b_base64, translate=string.translate
        ):
        return TimeStamp(a2b(translate(ts+'=',b64_untrans))).timeTime()

    def _getBrowserIdPieces(self, bid):
        """ returns browser id parts in a tuple consisting of rand_id,
        timestamp
        """
        return (bid[:8], bid[8:19])

    def _isAWellFormedBrowserId(self, bid, binerr=binascii.Error,
                                timestamperr=TimeStamp.error):
        try:
            rnd, ts = self._getBrowserIdPieces(bid)
            int(rnd)
            self._getB64TStampToInt(ts)
            return bid
        except (TypeError, ValueError, AttributeError, IndexError, binerr,
                timestamperr):
            return None

    def _setId(self, id):
        if id != self.id:
            raise Globals.MessageDialog(
                title='Cannot rename',
                message='You cannot rename a browser id manager, sorry!',
                action ='./manage_main',)


Globals.InitializeClass(BrowserIdManager)
