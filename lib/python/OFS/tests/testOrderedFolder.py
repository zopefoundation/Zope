from unittest import TestCase, TestSuite, makeSuite, main

import Testing
import Zope2
Zope2.startup()
from Interface.Verify import verifyClass

from OFS.OrderedFolder import OrderedFolder


class TestOrderedFolder(TestCase):

    def test_interface(self):
        from OFS.IOrderSupport import IOrderedContainer
        from webdav.WriteLockInterface import WriteLockInterface

        verifyClass(IOrderedContainer, OrderedFolder)
        verifyClass(WriteLockInterface, OrderedFolder)


def test_suite():
    return TestSuite( ( makeSuite(TestOrderedFolder), ) )

if __name__ == '__main__':
    main(defaultTest='test_suite')
