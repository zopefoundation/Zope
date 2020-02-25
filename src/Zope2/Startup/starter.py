##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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

import codecs
import locale
import logging

from ZConfig import ConfigurationError
from Zope2.Startup.handlers import _name_to_ips
from zope.event import notify
from zope.processlifetime import ProcessStarting


logger = logging.getLogger("Zope")


class WSGIStarter:
    """This is a class which starts Zope as a WSGI app."""

    wsgi = True

    def prepare(self):
        self.setupLocale()
        self.setupSecurityOptions()
        self.setupPublisher()
        self.setupInterpreter()
        self.startZope()
        from App.config import getConfiguration
        config = getConfiguration()  # NOQA
        notify(ProcessStarting())
        logger.info('Ready to handle requests')

    def setConfiguration(self, cfg):
        self.cfg = cfg

    def setupInterpreter(self):
        # make changes to the python interpreter environment
        pass

    def setupLocale(self):
        # set a locale if one has been specified in the config, else read from
        # environment.

        # workaround to allow unicode encoding conversions in DTML
        dummy = codecs.lookup('utf-8')  # NOQA

        locale_id = self.cfg.locale

        try:
            locale.setlocale(locale.LC_ALL, locale_id or '')
        except locale.Error:
            raise ConfigurationError(
                'The specified locale "%s" is not supported by your'
                'system.\nSee your operating system documentation for '
                'more\ninformation on locale support.' % locale_id)

    def setupPublisher(self):
        import ZPublisher.HTTPRequest
        from ZPublisher import WSGIPublisher
        WSGIPublisher.set_default_debug_mode(self.cfg.debug_mode)
        WSGIPublisher.set_default_debug_exceptions(self.cfg.debug_exceptions)
        WSGIPublisher.set_default_authentication_realm(
            self.cfg.http_realm)
        WSGIPublisher.set_webdav_source_port(self.cfg.webdav_source_port)
        if self.cfg.trusted_proxies:
            mapped = []
            for name in self.cfg.trusted_proxies:
                mapped.extend(_name_to_ips(name))
            ZPublisher.HTTPRequest.trusted_proxies = tuple(mapped)

    def setupSecurityOptions(self):
        import AccessControl
        AccessControl.setImplementation(
            self.cfg.security_policy_implementation)
        AccessControl.setDefaultBehaviors(
            not self.cfg.skip_ownership_checking,
            not self.cfg.skip_authentication_checking,
            self.cfg.verbose_security)

    def startZope(self):
        # Import Zope
        import Zope2
        Zope2.startup_wsgi()
