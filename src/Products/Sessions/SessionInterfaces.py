############################################################################
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
############################################################################
# BBB location for APIs now defined in Products.Sessions.interfaces

from Products.Sessions.interfaces import IBrowserIdManager
BrowserIdManagerInterface = IBrowserIdManager # BBB

from Products.Sessions.interfaces import ISessionDataManager
SessionDataManagerInterface = ISessionDataManager

from Products.Sessions.interfaces import SessionDataManagerErr
from Products.Sessions.interfaces import BrowserIdManagerErr
