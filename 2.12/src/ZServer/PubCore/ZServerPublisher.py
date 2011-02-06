##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import logging

LOG = logging.getLogger('ZServerPublisher')

class ZServerPublisher:
    def __init__(self, accept):
        from sys import exc_info
        from ZPublisher import publish_module
        from ZPublisher.WSGIPublisher import publish_module as publish_wsgi
        while 1:
          try:
            name, a, b=accept()
            if name == "Zope2":
                try:
                    publish_module(
                        name,
                        request=a,
                        response=b)
                finally:
                    b._finish()
                    a=b=None

            elif name == "Zope2WSGI":
                try:
                    res = publish_wsgi(a, b)
                    for r in res:
                        a['wsgi.output'].write(r)
                finally:
                    # TODO: Support keeping connections open.
                    a['wsgi.output']._close = 1
                    a['wsgi.output'].close()
          except:
            LOG.error('exception caught', exc_info=True)
