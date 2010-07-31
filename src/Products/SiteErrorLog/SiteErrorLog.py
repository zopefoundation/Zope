##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Site error log module.
"""

import os
import sys
import time
import logging
from random import random
from thread import allocate_lock

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.unauthorized import Unauthorized
from Acquisition import aq_base
from App.Dialogs import MessageDialog
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zExceptions.ExceptionFormatter import format_exception

LOG = logging.getLogger('Zope.SiteErrorLog')

# Permission names
use_error_logging = 'Log Site Errors'
log_to_event_log = 'Log to the Event Log'

# We want to restrict the rate at which errors are sent to the Event Log
# because we know that these errors can be generated quick enough to
# flood some zLOG backends. zLOG is used to notify someone of a problem,
# not to record every instance.
# This dictionary maps exception name to a value which encodes when we
# can next send the error with that name into the event log. This dictionary
# is shared between threads and instances. Concurrent access will not
# do much harm.
_rate_restrict_pool = {}

# The number of seconds that must elapse on average between sending two
# exceptions of the same name into the the Event Log. one per minute.
_rate_restrict_period = 60

# The number of exceptions to allow in a burst before the above limit
# kicks in. We allow five exceptions, before limiting them to one per
# minute.
_rate_restrict_burst = 5

_www = os.path.join(os.path.dirname(__file__), 'www')

# temp_logs holds the logs.
temp_logs = {}  # { oid -> [ traceback string ] }

cleanup_lock = allocate_lock()


class SiteErrorLog (SimpleItem):
    """Site error log class.  You can put an error log anywhere in the tree
    and exceptions in that area will be posted to the site error log.
    """
    meta_type = 'Site Error Log'
    id = 'error_log'

    keep_entries = 20
    copy_to_zlog = True

    security = ClassSecurityInfo()

    manage_options = (
        {'label': 'Log', 'action': 'manage_main'},
        ) + SimpleItem.manage_options

    security.declareProtected(use_error_logging, 'manage_main')
    manage_main = PageTemplateFile('main.pt', _www)

    security.declareProtected(use_error_logging, 'showEntry')
    showEntry = PageTemplateFile('showEntry.pt', _www)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        if item is self:
            try:
                del container.__error_log__
            except AttributeError:
                pass

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        if item is self:
            container.__error_log__ = aq_base(self)

    def _setId(self, id):
        if id != self.id:
            raise ValueError(MessageDialog(
                title='Invalid Id',
                message='Cannot change the id of a SiteErrorLog',
                action='./manage_main'))

    def _getLog(self):
        """Returns the log for this object.

        Careful, the log is shared between threads.
        """
        log = temp_logs.get(self._p_oid, None)
        if log is None:
            log = []
            temp_logs[self._p_oid] = log
        return log

    security.declareProtected(use_error_logging, 'forgetEntry')
    def forgetEntry(self, id, REQUEST=None):
        """Removes an entry from the error log."""
        log = self._getLog()
        cleanup_lock.acquire()
        i=0
        for entry in log:
            if entry['id'] == id:
                del log[i]
            i += 1
        cleanup_lock.release()
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(
                '%s/manage_main?manage_tabs_message=Error+log+entry+was+removed.' %
                self.absolute_url())

    # Exceptions that happen all the time, so we dont need
    # to log them. Eventually this should be configured
    # through-the-web.
    _ignored_exceptions = ( 'Unauthorized', 'NotFound', 'Redirect' )

    security.declarePrivate('raising')
    def raising(self, info):
        """Log an exception.

        Called by SimpleItem's exception handler.
        Returns the url to view the error log entry
        """
        try:
            now = time.time()
            try:
                tb_text = None
                tb_html = None

                strtype = str(getattr(info[0], '__name__', info[0]))
                if strtype in self._ignored_exceptions:
                    return

                if not isinstance(info[2], basestring):
                    tb_text = ''.join(
                        format_exception(*info, **{'as_html': 0}))
                    tb_html = ''.join(
                        format_exception(*info, **{'as_html': 1}))
                else:
                    tb_text = info[2]

                request = getattr(self, 'REQUEST', None)
                url = None
                username = None
                userid   = None
                req_html = None
                try:
                    strv = str(info[1])
                except:
                    strv = '<unprintable %s object>' % type(info[1]).__name__
                if request:
                    url = request.get('URL', '?')
                    usr = getSecurityManager().getUser()
                    username = usr.getUserName()
                    userid = usr.getId()
                    try:
                        req_html = str(request)
                    except:
                        pass
                    if strtype == 'NotFound':
                        strv = url
                        next = request['TraversalRequestNameStack']
                        if next:
                            next = list(next)
                            next.reverse()
                            strv = '%s [ /%s ]' % (strv, '/'.join(next))

                log = self._getLog()
                entry_id = str(now) + str(random()) # Low chance of collision
                log.append({
                    'type': strtype,
                    'value': strv,
                    'time': now,
                    'id': entry_id,
                    'tb_text': tb_text,
                    'tb_html': tb_html,
                    'username': username,
                    'userid': userid,
                    'url': url,
                    'req_html': req_html,
                    })

                cleanup_lock.acquire()
                try:
                    if len(log) >= self.keep_entries:
                        del log[:-self.keep_entries]
                finally:
                    cleanup_lock.release()
            except:
                LOG.error('Error while logging', exc_info=sys.exc_info())
            else:
                if self.copy_to_zlog:
                    self._do_copy_to_zlog(now,strtype,entry_id,str(url),tb_text)
                return '%s/showEntry?id=%s' % (self.absolute_url(), entry_id)
        finally:
            info = None

    def _do_copy_to_zlog(self,now,strtype,entry_id,url,tb_text):
        when = _rate_restrict_pool.get(strtype,0)
        if now>when:
            next_when = max(when, now-_rate_restrict_burst*_rate_restrict_period)
            next_when += _rate_restrict_period
            _rate_restrict_pool[strtype] = next_when
            LOG.error('%s %s\n%s' % (entry_id, url, tb_text.rstrip()))

    security.declareProtected(use_error_logging, 'getProperties')
    def getProperties(self):
        return {
            'keep_entries': self.keep_entries,
            'copy_to_zlog': self.copy_to_zlog,
            'ignored_exceptions': self._ignored_exceptions,
            }

    security.declareProtected(log_to_event_log, 'checkEventLogPermission')
    def checkEventLogPermission(self):
        if not getSecurityManager().checkPermission(log_to_event_log, self):
            raise Unauthorized, ('You do not have the "%s" permission.' %
                                 log_to_event_log)
        return 1

    security.declareProtected(use_error_logging, 'setProperties')
    def setProperties(self, keep_entries, copy_to_zlog=0,
                      ignored_exceptions=(), RESPONSE=None):
        """Sets the properties of this site error log.
        """
        copy_to_zlog = not not copy_to_zlog
        if copy_to_zlog and not self.copy_to_zlog:
            # Before turning on event logging, check the permission.
            self.checkEventLogPermission()
        self.keep_entries = int(keep_entries)
        self.copy_to_zlog = copy_to_zlog
        self._ignored_exceptions = tuple(
            filter(None, map(str, ignored_exceptions)))
        if RESPONSE is not None:
            RESPONSE.redirect(
                '%s/manage_main?manage_tabs_message=Changed+properties.' %
                self.absolute_url())

    security.declareProtected(use_error_logging, 'getLogEntries')
    def getLogEntries(self):
        """Returns the entries in the log, most recent first.

        Makes a copy to prevent changes.
        """
        # List incomprehension ;-)
        res = [entry.copy() for entry in self._getLog()]
        res.reverse()
        return res

    security.declareProtected(use_error_logging, 'getLogEntryById')
    def getLogEntryById(self, id):
        """Returns the specified log entry.

        Makes a copy to prevent changes.  Returns None if not found.
        """
        for entry in self._getLog():
            if entry['id'] == id:
                return entry.copy()
        return None

    security.declareProtected(use_error_logging, 'getLogEntryAsText')
    def getLogEntryAsText(self, id, RESPONSE=None):
        """Returns the specified log entry.

        Makes a copy to prevent changes.  Returns None if not found.
        """
        entry = self.getLogEntryById(id)
        if entry is None:
            return 'Log entry not found or expired'
        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', 'text/plain')
        return entry['tb_text']

InitializeClass(SiteErrorLog)


def manage_addErrorLog(dispatcher, RESPONSE=None):
    """Add a site error log to a container."""
    log = SiteErrorLog()
    dispatcher._setObject(log.id, log)
    if RESPONSE is not None:
        RESPONSE.redirect(
            dispatcher.DestinationURL() +
            '/manage_main?manage_tabs_message=Error+Log+Added.' )
