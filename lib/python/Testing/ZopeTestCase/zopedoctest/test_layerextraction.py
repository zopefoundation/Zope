from Testing.ZopeTestCase import ZopeDocFileSuite as FileSuite
from Testing.ZopeTestCase import ZopeDocTestSuite as TestSuite
from Testing.ZopeTestCase.ZopeTestCase import ZopeTestCase
from Testing import ZopeTestCase

import transaction as txn

class TestLayer:
    """
    If the layer is extracted properly, we should see the following
    variable

    >>> getattr(self.app, 'LAYER_EXTRACTED', False)
    True
    """
    @classmethod
    def setUp(cls):
        app = ZopeTestCase.app()
        app.LAYER_EXTRACTED = True
        txn.commit()
        ZopeTestCase.close(app)

    @classmethod
    def tearDown(cls):
        app = ZopeTestCase.app()
        del app.LAYER_EXTRACTED
        txn.commit()
        ZopeTestCase.close(app)

class TestCase(ZopeTestCase.ZopeTestCase):
    layer = TestLayer

def test_suite():
    import unittest
    fs = FileSuite('layerextraction.txt',
                   test_class=TestCase,
                   package='Testing.ZopeTestCase.zopedoctest'
                   )
    ts = TestSuite('Testing.ZopeTestCase.zopedoctest.test_layerextraction',
                   test_class=TestCase,
                   )
    return unittest.TestSuite((fs, ts))
