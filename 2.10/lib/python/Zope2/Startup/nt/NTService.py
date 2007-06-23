##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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

"""
Compatibility stub (Zope 2.7's up to b1 used to keep all nt service-related
files here; they've since moved to ntservice_utils)
"""

from nt_svcutils import service
import win32serviceutil

# this is a class which instance services subclass
ZopeService = service.Service

if __name__=='__main__':
    win32serviceutil.HandleCommandLine(ZopeService)

