##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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

"""Datatypes for the Zope schema for use with ZConfig."""

import os

# generic datatypes

def security_policy_implementation(value):
    value = value.upper()
    ok = ('PYTHON', 'C')
    if value not in ok:
        raise ValueError, (
            "security_policy_implementation must be one of %s" % ok
            )
    return value

def cgi_environment(section):
    return section.environ

# Datatype for the access and trace logs
# (the loghandler datatypes come from the zLOG package)

class LoggerFactory:
    """
    A factory used to create loggers while delaying actual logger
    instance construction.  We need to do this because we may want to
    reference a logger before actually instantiating it (for example,
    to allow the app time to set an effective user).  An instance of
    this wrapper is a callable which, when called, returns a logger
    object.
    """
    def __init__(self, section):
        self.name = section.getSectionName()
        self.level = section.level
        self.handler_factories = section.handlers
        self.resolved = None

    def __call__(self):
        if self.resolved is None:
            # set the logger up
            import logging
            logger = logging.getLogger(self.name)
            logger.handlers = []
            logger.propagate = 0
            logger.setLevel(self.level)
            for handler_factory in self.handler_factories:
                handler = handler_factory()
                logger.addHandler(handler)
            self.resolved = logger
        return self.resolved

# DNS resolver

def dns_resolver(hostname):
    from ZServer.medusa import resolver
    return resolver.caching_resolver(hostname)


# Datatype for the root configuration object
# (adds the softwarehome and zopehome fields; default values for some
#  computed paths)

def root_config(section):
    here = os.path.dirname(os.path.abspath(__file__))
    swhome = os.path.dirname(os.path.dirname(here))
    section.softwarehome = swhome
    section.zopehome = os.path.dirname(os.path.dirname(swhome))
    if section.cgi_environment is None:
        section.cgi_environment = {}
    if section.clienthome is None:
        section.clienthome = os.path.join(section.instancehome, "var")
    # set up defaults for pid_filename and lock_filename if they're
    # not in the config
    if section.pid_filename is None:
        section.pid_filename = os.path.join(section.clienthome, 'Z2.pid')
    if section.lock_filename is None:
        section.lock_filename = os.path.join(section.clienthome, 'Z2.lock')
    return section
