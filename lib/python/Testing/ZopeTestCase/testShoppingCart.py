##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Example ZopeTestCase testing the ShoppingCart example application

Note the use of sessions and how the SESSION object is added to
the REQUEST in afterSetUp().

You can use zLOG.LOG() if you set up the event log variables first.
Handy for debugging and tracing your tests.

$Id$
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

#os.environ['STUPID_LOG_FILE'] = os.path.join(os.getcwd(), 'zLOG.log')
#os.environ['STUPID_LOG_SEVERITY'] = '0'

from Testing import ZopeTestCase

from Globals import SOFTWARE_HOME
examples_path = os.path.join(SOFTWARE_HOME, '..', '..', 'skel', 'import', 'Examples.zexp')
examples_path = os.path.abspath(examples_path)


# Open ZODB connection
app = ZopeTestCase.app()

# Set up sessioning objects
ZopeTestCase.utils.setupCoreSessions(app)

# Set up example applications
if not hasattr(app, 'Examples'):
    ZopeTestCase.utils.importObjectFromFile(app, examples_path)

# Close ZODB connection
ZopeTestCase.close(app)


class DummyOrder:
    '''Construct an order we can add to the cart'''
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, id, quantity):
        self.id = id
        self.quantity = quantity


class TestShoppingCart(ZopeTestCase.ZopeTestCase):
    '''Test the ShoppingCart example application'''

    _setup_fixture = 0  # No default fixture

    def afterSetUp(self):
        self.cart = self.app.Examples.ShoppingCart
        # Put SESSION object into REQUEST
        request = self.app.REQUEST
        sdm = self.app.session_data_manager
        request.set('SESSION', sdm.getSessionData())
        self.session = request.SESSION

    def testSession(self):
        # Session should work
        self.session.set('boring', 'boring')
        self.assertEqual(self.session.get('boring'), 'boring')

    def testCartIsEmpty(self):
        # Cart should be empty
        self.assertEqual(len(self.cart.currentItems()), 0)

    def testAddItems(self):
        # Adding to the cart should work
        self.cart.addItems([DummyOrder('510-115', 1),])
        self.assertEqual(len(self.cart.currentItems()), 1)

    def testDeleteItems(self):
        # Deleting from the cart should work
        self.cart.addItems([DummyOrder('510-115', 1),])
        self.cart.deleteItems(['510-115'])
        self.assertEqual(len(self.cart.currentItems()), 0)

    def testAddQuantity(self):
        # Adding to quantity should work
        self.cart.addItems([DummyOrder('510-115', 1),])
        self.cart.addItems([DummyOrder('510-115', 2),])
        self.cart.addItems([DummyOrder('510-115', 3),])
        self.assertEqual(self.cart.currentItems()[0]['quantity'], 6)

    def testGetTotal(self):
        # Totals should be computed correctly
        self.cart.addItems([DummyOrder('510-115', 1),])
        self.cart.addItems([DummyOrder('510-122', 2),])
        self.cart.addItems([DummyOrder('510-007', 2),])
        self.assertEqual(self.cart.getTotal(), 149.95)

    def testGetItem(self):
        # Getting an item from the "database" should work
        item = self.cart.getItem('510-115')
        self.assertEqual(item['id'], '510-115')
        self.assertEqual(item['title'], 'Econo Feeder')
        self.assertEqual(item['price'], 7.95)

    def testEight(self):
        # Additional test to trigger connection pool depletion bug
        pass


class TestSandboxedShoppingCart(ZopeTestCase.Sandboxed, TestShoppingCart):
    '''Demonstrate that sessions work in sandboxes''' 


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestShoppingCart))
    suite.addTest(makeSuite(TestSandboxedShoppingCart))
    return suite

if __name__ == '__main__':
    framework()

