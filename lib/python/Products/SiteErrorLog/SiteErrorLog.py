##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
# 
##############################################################################
"""Site error log module.

$Id: SiteErrorLog.py,v 1.4 2002/04/05 16:01:55 htrd Exp $
"""

import os
import sys
import time
from random import random
from thread import allocate_lock
from types import StringType, UnicodeType

import Globals
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo, getSecurityManager, Unauthorized
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zExceptions.ExceptionFormatter import format_exception
from zLOG import LOG, ERROR

# Permission names
use_error_logging = 'Log Site Errors'
log_to_event_log = 'Log to the Event Log'


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
    copy_to_zlog = 0

    security = ClassSecurityInfo()

    manage_options = (
        {'label': 'Log', 'action': 'manage_main'},
        ) + SimpleItem.manage_options

    security.declareProtected(use_error_logging, 'getProperties')
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
            raise Globals.MessageDialog(
                title='Invalid Id',
                message='Cannot change the id of a SiteErrorLog',
                action ='./manage_main',)

    def _getLog(self):
        """Returns the log for this object.

        Careful, the log is shared between threads.
        """
        log = temp_logs.get(self._p_oid, None)
        if log is None:
            log = []
            temp_logs[self._p_oid] = log
        return log

    security.declarePrivate('raising')
    def raising(self, info):
        """Log an exception.

        Called by SimpleItem's exception handler.
        """
        try:
            now = time.time()
            try:
                tb_text = None
                tb_html = None

                if not isinstance(info[2], StringType) and not isinstance(
                    info[2], UnicodeType):
                    tb_text = ''.join(
                        format_exception(*info, **{'as_html': 0}))
                    tb_html = ''.join(
                        format_exception(*info, **{'as_html': 1}))
                else:
                    tb_text = info[2]

                request = getattr(self, 'REQUEST', None)
                url = None
                username = None
                req_html = None
                if request:
                    url = request['URL']
                    username = getSecurityManager().getUser().getUserName()
                    try:
                        req_html = str(request)
                    except:
                        pass

                try:
                    strv = str(info[1])
                except:
                    strv = '<unprintable %s object>' % str(type(info[1]).__name__)

                log = self._getLog()
                log.append({
                    'type': str(getattr(info[0], '__name__', info[0])),
                    'value': strv,
                    'time': now,
                    'id': str(now) + str(random()), # Low chance of collision
                    'tb_text': tb_text,
                    'tb_html': tb_html,
                    'username': username,
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
                LOG('SiteError', ERROR, 'Error while logging',
                    error=sys.exc_info())
            else:
                if self.copy_to_zlog:
                    LOG('SiteError', ERROR, str(url), error=info)
        finally:
            info = None

    security.declareProtected(use_error_logging, 'getProperties')
    def getProperties(self):
        return {'keep_entries': self.keep_entries,
                'copy_to_zlog': self.copy_to_zlog}

    security.declareProtected(log_to_event_log, 'checkEventLogPermission')
    def checkEventLogPermission(self):
        if not getSecurityManager().checkPermission(log_to_event_log, self):
            raise Unauthorized, ('You do not have the "%s" permission.' %
                                 log_to_event_log)
        return 1

    security.declareProtected(use_error_logging, 'setProperties')
    def setProperties(self, keep_entries, copy_to_zlog=0, RESPONSE=None):
        """Sets the properties of this site error log.
        """
        copy_to_zlog = not not copy_to_zlog
        if copy_to_zlog and not self.copy_to_zlog:
            # Before turning on event logging, check the permission.
            self.checkEventLogPermission()
        self.keep_entries = int(keep_entries)
        self.copy_to_zlog = copy_to_zlog
        if RESPONSE is not None:
            RESPONSE.redirect(
                '%s/manage_main?manage_tabs_message=Changed+properties.' %
                self.absolute_url())
    
    security.declareProtected(use_error_logging, 'getLogEntries')
    def getLogEntries(self):
        """Returns the entries in the log.

        Makes a copy to prevent changes.
        """
        # List incomprehension ;-)
        return [entry.copy() for entry in self._getLog()]

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


Globals.InitializeClass(SiteErrorLog)


def manage_addErrorLog(dispatcher, RESPONSE=None):
    """Add a site error log to a container."""
    log = SiteErrorLog()
    dispatcher._setObject(log.id, log)
    if RESPONSE is not None:
        RESPONSE.redirect(
            dispatcher.DestinationURL() +
            '/manage_main?manage_tabs_message=Error+Log+Added.' )

