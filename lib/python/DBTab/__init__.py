##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""DBTab product.

$Id: __init__.py,v 1.1 2003/07/20 02:55:58 chrism Exp $
"""

# importing ThreadedAsync has the side effect of patching asyncore so
# that loop callbacks get invoked.  You need this to
# mount a ZEO client connection if the main database is not a ZEO client.
# Otherwise ZEO never receives the message telling it to start using the
# main async loop.
import ThreadedAsync
