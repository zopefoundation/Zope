##############################################################################
#
# Copyright (c) 2023 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import pprint
import time
from operator import itemgetter

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from App.special_dtml import DTMLFile
from OFS.SimpleItem import Item


class ZODBConnectionDebugger(Item, Implicit):
    id = 'ZODBConnectionDebugger'
    name = title = 'ZODB Connections'
    meta_type = 'ZODB Connection Debugger'
    zmi_icon = 'fas fa-bug'

    security = ClassSecurityInfo()

    manage_zodb_conns = manage_main = manage = manage_workspace = DTMLFile(
        'dtml/zodbConnections', globals())
    manage_zodb_conns._setName('manage_zodb_conns')
    manage_options = (
        {'label': 'Control Panel', 'action': '../manage_main'},
        {'label': 'Databases', 'action': '../Database/manage_main'},
        {'label': 'Configuration', 'action': '../Configuration/manage_main'},
        {'label': 'DAV Locks', 'action': '../DavLocks/manage_main'},
        {'label': 'Reference Counts', 'action': '../DebugInfo/manage_main'},
        {'label': 'ZODB Connections', 'action': 'manage_main'},
    )

    def dbconnections(self):
        import Zope2  # for data

        result = []
        now = time.time()

        def get_info(connection):
            # `result`, `time` and `before` are lexically inherited.
            request_info = {}
            request_info_formatted = ''
            debug_info_formatted = ''
            opened = connection.opened
            debug_info = connection.getDebugInfo() or {}

            if debug_info:
                debug_info_formatted = pprint.pformat(debug_info)
                if len(debug_info) == 2:
                    request_info = debug_info[0]
                    request_info.update(debug_info[1])
                    request_info_formatted = pprint.pformat(request_info)

            if opened is not None:
                # output UTC time with the standard Z time zone indicator
                open_since = "{}".format(
                    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(opened)))
                open_for = f"{now - opened:.2f}s"
            else:
                open_since = '(closed)'
                open_for = ''

            result.append({
                'open_since': open_since,
                'open_for': open_for,
                'info': debug_info,
                'info_formatted': debug_info_formatted,
                'request_info': request_info,
                'request_formatted': request_info_formatted,
                'before': connection.before,
                'cache_size': len(connection._cache),
            })

        Zope2.DB._connectionMap(get_info)
        return sorted(result, key=itemgetter('open_since'))


InitializeClass(ZODBConnectionDebugger)
