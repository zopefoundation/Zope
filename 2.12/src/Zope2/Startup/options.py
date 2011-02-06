##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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

"""Command-line processor for Zope."""

import os

import zdaemon.zdoptions


class ZopeOptions(zdaemon.zdoptions.ZDOptions):
    """The Zope zdaemon runner script.

    Usage: python Zope2/run.py [-C URL][-h] [zdrun-options] [action [arguments]]

    Options:
    -C/--configure URL -- configuration file or URL
    -h/--help -- print usage message and exit
    -b/--backoff-limit SECONDS -- set backoff limit to SECONDS (default 10)
    -d/--daemon -- run as a proper daemon; fork a subprocess, close files etc.
    -f/--forever -- run forever (by default, exit when backoff limit is exceeded)
    -h/--help -- print this usage message and exit
    -s/--socket-name SOCKET -- Unix socket name for client (default "zdsock")
    -u/--user USER -- run as this user (or numeric uid)
    -m/--umask UMASK -- use this umask for daemon subprocess (default is 022)
    -x/--exit-codes LIST -- list of fatal exit codes (default "0,2")
    -z/--directory DIRECTORY -- directory to chdir to when using -d (default off)
    action [arguments] -- see below

    Actions are commands like "start", "stop" and "status".  If -i is
    specified or no action is specified on the command line, a "shell"
    interpreting actions typed interactively is started (unless the
    configuration option default_to_interactive is set to false).  Use the
    action "help" to find out about available actions.
    """

    schemadir = os.path.dirname(os.path.abspath(__file__))
    schemafile = "zopeschema.xml"
