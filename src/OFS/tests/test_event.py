##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
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
"""Test events
"""

# These classes aren't defined in the doctest because otherwise
# they wouldn't be picklable, and we need that to test copy/paste.

from OFS.SimpleItem import SimpleItem
from OFS.Folder import Folder
from OFS.OrderedFolder import OrderedFolder

from zope.component import testing, eventtesting

def setUp(test):
    testing.setUp(test)
    eventtesting.setUp(test)

class DontComplain(object):
    def _verifyObjectPaste(self, object, validate_src=1):
        pass
    def cb_isMoveable(self):
        return True
    def cb_isCopyable(self):
        return True

class NotifyBase(DontComplain):
    def manage_afterAdd(self, item, container):
        print 'old manage_afterAdd %s %s %s' % (self.getId(), item.getId(),
                                                container.getId())
        super(NotifyBase, self).manage_afterAdd(item, container)
    manage_afterAdd.__five_method__ = True # Shut up deprecation warnings
    def manage_beforeDelete(self, item, container):
        super(NotifyBase, self).manage_beforeDelete(item, container)
        print 'old manage_beforeDelete %s %s %s' % (self.getId(), item.getId(),
                                                    container.getId())
    manage_beforeDelete.__five_method__ = True # Shut up deprecation warnings
    def manage_afterClone(self, item):
        print 'old manage_afterClone %s %s' % (self.getId(), item.getId())
        super(NotifyBase, self).manage_afterClone(item)
    manage_afterClone.__five_method__ = True # Shut up deprecation warnings

class MyApp(Folder):
    def getPhysicalRoot(self):
        return self

class MyFolder(NotifyBase, Folder):
    pass

class MyOrderedFolder(NotifyBase, OrderedFolder):
    pass

class MyContent(NotifyBase, SimpleItem):
    def __init__(self, id):
        self._setId(id)

# These don't have manage_beforeDelete & co methods

class MyNewContent(DontComplain, SimpleItem):
    def __init__(self, id):
        self._setId(id)

class MyNewFolder(DontComplain, Folder):
    pass


def test_suite():
    from doctest import DocFileSuite
    return DocFileSuite('event.txt', package="OFS.tests",
                        setUp=setUp, tearDown=testing.tearDown)
