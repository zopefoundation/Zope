##############################################################################
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
##############################################################################

"""
$Id: ZCatalog.py 25050 2004-05-27 15:06:40Z chrisw $
"""

class ProgressHandler:
    """ A simple machinery to provide progres informations for long running
        ZCatalog operations like reindexing.
    """

    def pg_register(self, handler=None):
        self._v_pg_handler = handler


    def pg_init(self, max):
        handler = getattr(self, '_v_pg_handler', None)
        if not handler: return
        handler.init(max)

    def pg_finish(self):
        handler = getattr(self, '_v_pg_handler', None)
        if not handler: return
        handler.finish()

    def pg_report(self, current, *args, **kw):
        handler = getattr(self, '_v_pg_handler', None)
        if not handler: return
        handler.report(current, *args, **kw)
