#!python
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
"""Start Zope.  Now!"""

import App.config

from Zope.Startup import handlers, options, start_zope


def main():
    opts = options.ZopeOptions()
    opts.realize()
    handlers.handleConfig(opts.configroot, opts.confighandlers)
    App.config.setConfiguration(opts.configroot)
    start_zope(opts.configroot)


if __name__ == "__main__":
    main()
