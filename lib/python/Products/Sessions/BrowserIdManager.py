############################################################################
# 
# Zope Public License (ZPL) Version 1.1
# -------------------------------------
# 
# Copyright (c) Zope Corporation.  All rights reserved.
# 
# This license has been certified as open source.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Zope Corporation 
#      for use in the Z Object Publishing Environment
#      (http://www.zope.com/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 4. Names associated with Zope or Zope Corporation must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Zope Corporation.
# 
# 5. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Zope Corporation
#      for use in the Z Object Publishing Environment
#      (http://www.zope.com/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 6. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY ZOPE CORPORATION ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL ZOPE CORPORATION OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Zope Corporation and
# many individuals on behalf of Zope Corporation.  Specific
# attributions are listed in the accompanying credits file.
#
############################################################################

__version__='$Revision: 1.3 $'[11:-2]
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

b64_trans = string.maketrans('+/', '-.')
b64_untrans = string.maketrans('-.', '+/')

badtokenkeycharsin = re.compile('[\?&;, ]').search
badcookiecharsin = re.compile('[;, ]').search
twodotsin = re.compile('(\w*\.){2,}').search

_marker = []

constructBrowserIdManagerForm = Globals.DTMLFile('dtml/addIdManager',globals())

ADD_BROWSER_ID_MANAGER_PERM="Add Browser ID Manager"

def constructBrowserIdManager(
    self, id, title='', tokenkey='_ZopeId', cookiepri=1, formpri=2,
    urlpri=0, cookiepath='/', cookiedomain='', cookielifedays=0,
    cookiesecure=0, REQUEST=None
    ):
    """ """
    # flip dictionary and take what's not 0 (god I hate HTML)
    d = {}
    for k,v in {'url':urlpri, 'form':formpri, 'cookies':cookiepri}.items():
        if v: d[v] = k
    ob = BrowserIdManager(id, title, tokenkey, d, cookiepath,
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

    security = ClassSecurityInfo()
    security.setDefaultAccess('deny')
    security.setPermissionDefault(MGMT_SCREEN_PERM, ['Manager'])
    security.setPermissionDefault(ACCESS_CONTENTS_PERM,['Manager','Anonymous'])
    security.setPermissionDefault(CHANGE_IDMGR_PERM, ['Manager'])

    __replaceable__ = UNIQUE # singleton for now

    __implements__ = (SessionInterfaces.BrowserIdManagerInterface, )

    icon = 'misc_/Sessions/idmgr.gif'

    def __init__(
        self, id, title='', tokenkey='_ZopeId',
        tokenkeynamespaces={1:'cookies',2:'form'}, cookiepath=('/'),
        cookiedomain='', cookielifedays=0, cookiesecure=0, on=1
        ):

        self.id = id
        self.title = title
        self.setTokenKey(tokenkey)
        self.setTokenKeyNamespaces(tokenkeynamespaces)
        self.setCookiePath(cookiepath)
        self.setCookieDomain(cookiedomain)
        self.setCookieLifeDays(cookielifedays)
        self.setCookieSecure(cookiesecure)
        if on:
            self.turnOn()
        else:
            self.turnOff()

    # delegating methods follow
    # don't forget to change the name of the method in
    # delegation if you change a delegating method name

    security.declareProtected(ACCESS_CONTENTS_PERM, 'hasToken')
    def hasToken(self):
        """ Returns true if there is a current browser token, but does
        not create a browser token for the current request if one doesn't
        already exist """
        if not self.on:
            return self._delegateToParent('hasToken')
        if self.getToken(create=0): return 1
                
    security.declareProtected(ACCESS_CONTENTS_PERM, 'getToken')
    def getToken(self, create=1):
        """
        Examines the request and hands back browser token value or
        None if no token exists.  If there is no browser token
        and if 'create' is true, create one.  If cookies are are
        an allowable id key namespace and create is true, set one.  Stuff
        the token and the namespace it was found in into the REQUEST object
        for further reference during this request.  Delegate this call to
        a parent if we're turned off.
        """
        if not self.on:
            return self._delegateToParent('getToken', create)
        REQUEST = self.REQUEST
        # let's see if token has already been attached to request
        token = getattr(REQUEST, 'browser_token_', None)
        if token is not None:
            # it's already set in this request so we can just return it
            # if it's well-formed
            if not self._isAWellFormedToken(token):
                # somebody screwed with the REQUEST instance during
                # this request.
                raise BrowserIdManagerErr, (
                    'Ill-formed token in REQUEST.browser_token_:  %s' % token
                    )
            return token
        # fall through & ck id key namespaces if token is not in request.
        tk = self.token_key
        ns = self.token_key_namespaces
        for name in ns:
            token = getattr(REQUEST, name).get(tk, None)
            if token is not None:
                # hey, we got a token!
                if self._isAWellFormedToken(token):
                    # token is not "plain old broken"
                    REQUEST.browser_token_ = token
                    REQUEST.browser_token_ns_ = name
                    return token
        # fall through if token is invalid or not in key namespaces
        if create:
            # create a brand new token
            token = self._getNewToken()
            if 'cookies' in ns:
                self._setCookie(token, REQUEST)
            REQUEST.browser_token_ = token
            REQUEST.browser_token_ns_ = None
            return token
        # implies a return of None if:
        # (not create=1) and (invalid or ((not in req) and (not in ns)))

    security.declareProtected(ACCESS_CONTENTS_PERM, 'flushTokenCookie')
    def flushTokenCookie(self):
        """ removes the token cookie from the client browser """
        if not self.on:
            return self._delegateToParent('flushToken')
        if 'cookies' not in self.token_key_namespaces:
            raise BrowserIdManagerErr,('Cookies are not now being used as a '
                                       'browser token key namespace, thus '
                                       'the token cookie cannot be flushed.')
        self._setCookie('deleted', self.REQUEST, remove=1)

    security.declareProtected(ACCESS_CONTENTS_PERM, 'isTokenFromCookie')
    def isTokenFromCookie(self):
        """ returns true if browser token is from REQUEST.cookies """
        if not self.on:
            return self._delegateToParent('isTokenFromCookie')
        if not self.getToken(): # make sure the token is stuck on REQUEST
            raise BrowserIdManagerErr, 'There is no current browser token.'
        if getattr(self.REQUEST, 'browser_token_ns_') == 'cookies':
            return 1

    security.declareProtected(ACCESS_CONTENTS_PERM, 'isTokenFromForm')
    def isTokenFromForm(self):
        """ returns true if browser token is from REQUEST.form """
        if not self.on:
            return self._delegateToParent('isTokenFromForm')
        if not self.getToken(): # make sure the token is stuck on REQUEST
            raise BrowserIdManagerErr, 'There is no current browser token.'
        if getattr(self.REQUEST, 'browser_token_ns_') == 'form':
            return 1

    security.declareProtected(ACCESS_CONTENTS_PERM, 'isTokenNew')
    def isTokenNew(self):
        """
        returns true if browser token is 'new', meaning the token exists
        but it has not yet been acknowledged by the client (the client
        hasn't sent it back to us in a cookie or in a formvar).
        """
        if not self.on:
            return self._delegateToParent('isTokenNew')
        if not self.getToken(): # make sure the token is stuck on REQUEST
            raise BrowserIdManagerErr, 'There is no current browser token.'
        # ns will be None if new, negating None below returns 1, which
        # would indicate that it's new on this request
        return not getattr(self.REQUEST, 'browser_token_ns_')
    
    security.declareProtected(ACCESS_CONTENTS_PERM, 'encodeUrl')
    def encodeUrl(self, url, create=1):
        """
        encode a URL with the browser key as a postfixed query string
        element
        """
        if not self.on:
            return self._delegateToParent('encodeUrl', url)
        token = self.getToken(create)
        if token is None:
            raise BrowserIdManagerErr, 'There is no current browser token.'
        key = self.getTokenKey()
        if '?' in url:
            return '%s&%s=%s' % (url, key, token)
        else:
            return '%s?%s=%s' % (url, key, token)

    # non-delegating methods follow

    security.declareProtected(MGMT_SCREEN_PERM, 'manage_browseridmgr')
    manage_browseridmgr = Globals.DTMLFile('dtml/manageIdManager', globals())

    security.declareProtected(CHANGE_IDMGR_PERM,
                              'manage_changeBrowserIdManager')
    def manage_changeBrowserIdManager(
        self, title='', tokenkey='_ZopeId', cookiepri=1, formpri=2,
        cookiepath='/', cookiedomain='', cookielifedays=0, cookiesecure=0,
        on=0, REQUEST=None
        ):
        """ """
        d = {}
        for k,v in {'cookies':cookiepri, 'form':formpri}.items():
            if v: d[v] = k # I hate HTML
        self.title = title
        self.setTokenKey(tokenkey)
        self.setTokenKeyNamespaces(d)
        self.setCookiePath(cookiepath)
        self.setCookieDomain(cookiedomain)
        self.setCookieLifeDays(cookielifedays)
        self.setCookieSecure(cookiesecure)
        if on:
            self.turnOn()
        else:
            self.turnOff()
        if REQUEST is not None:
            return self.manage_browseridmgr(self, REQUEST)

    security.declareProtected(CHANGE_IDMGR_PERM, 'setTokenKey')
    def setTokenKey(self, k):
        """ sets browser token key string """
        if not (type(k) is type('') and k and not badtokenkeycharsin(k)):
            raise BrowserIdManagerErr, 'Bad id key string %s' % repr(k)
        self.token_key = k

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getTokenKey')
    def getTokenKey(self):
        """ """
        return self.token_key

    security.declareProtected(CHANGE_IDMGR_PERM, 'setTokenKeyNamespaces')
    def setTokenKeyNamespaces(self,namespacesd={1:'cookies',2:'form'}):
        """
        accepts dictionary e.g. {1: 'cookies', 2: 'form'} as token
        id key allowable namespaces and lookup ordering priority
        where key is 'priority' with 1 being highest.
        """
        allowed = self.getAllTokenKeyNamespaces()
        for name in namespacesd.values():
            if name not in allowed:
                raise BrowserIdManagerErr, (
                    'Bad id key namespace %s' % repr(name)
                    )
        self.token_key_namespaces = []
        nskeys = namespacesd.keys()
        nskeys.sort()
        for priority in nskeys:
            self.token_key_namespaces.append(namespacesd[priority])

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getTokenKeyNamespaces')
    def getTokenKeyNamespaces(self):
        """ """
        d = {}
        i = 1
        for name in self.token_key_namespaces:
            d[i] = name
            i = i + 1
        return d

    security.declareProtected(CHANGE_IDMGR_PERM, 'setCookiePath')
    def setCookiePath(self, path=''):
        """ sets cookie 'path' element for id cookie """
        if not (type(path) is type('') and not badcookiecharsin(path)):
            raise BrowserIdManagerErr, 'Bad cookie path %s' % repr(path)
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
                % repr(days)
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
                'Cookie domain must be string: %s' % repr(domain)
                )
        if not domain:
            self.cookie_domain = ''
            return
        if not twodotsin(domain):
            raise BrowserIdManagerErr, (
                'Cookie domain must contain at least two dots (e.g. '
                '".zope.org" or "www.zope.org") or it must be left blank. : '
                '%s' % `domain`
                )
        if badcookiecharsin(domain):
            raise BrowserIdManagerErr, (
                'Bad characters in cookie domain %s' % `domain`
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

    security.declareProtected(ACCESS_CONTENTS_PERM, 'getAllTokenKeyNamespaces')
    def getAllTokenKeyNamespaces(self):
        """
        These are the REQUEST namespaces searched when looking for an
        id key value.
        """
        return ('form', 'cookies')

    security.declareProtected(CHANGE_IDMGR_PERM, 'turnOn')
    def turnOn(self):
        """ """
        self.on = 1

    security.declareProtected(CHANGE_IDMGR_PERM, 'turnOff')
    def turnOff(self):
        """ """
        self.on = 0

    security.declareProtected(ACCESS_CONTENTS_PERM, 'isOn')
    def isOn(self):
        """ """
        return self.on

    # non-interface methods follow

    def _getNewToken(self, randint=random.randint, maxint=99999999):
        """ Returns 19-character string browser token
        'AAAAAAAABBBBBBBB'
        where:

        A == leading-0-padded 8-char string-rep'd random integer
        B == modified base64-encoded 11-char timestamp
        
        To be URL-compatible, base64 encoding is modified as follows:
          '=' end-padding is stripped off
          '+' is translated to '-'
          '/' is translated to '.'
        """
        return '%08i%s' % (randint(0, maxint-1), self._getB64TStamp())
    
    def _delegateToParent(self, *arg, **kw):
        fn = arg[0]
        rest = arg[1:]
        try:
            parent_sessidmgr=getattr(self.aq_parent, self.id)
            parent_fn = getattr(parent_sessidmgr, fn)
        except AttributeError:
            raise BrowserIdManagerErr, 'Browser id management disabled'
        return apply(parent_fn, rest, kw)

    def _setCookie(
        self, token, REQUEST, remove=0, now=time.time, strftime=time.strftime,
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
        cookie = cookies[self.token_key]= {}
        for k,v in d.items():
            if v:
                cookie[k] = v #only stuff things with true values
        cookie['value'] = token
        
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

    def _getTokenPieces(self, token):
        """ returns browser token parts in a tuple consisting of rand_id,
        timestamp
        """
        return (token[:8], token[8:19])

    def _isAWellFormedToken(self, token, binerr=binascii.Error,
                            timestamperr=TimeStamp.error):
        try:
            rnd, ts = self._getTokenPieces(token)
            int(rnd)
            self._getB64TStampToInt(ts)
            return token
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
