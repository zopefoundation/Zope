import types
import unittest
from pathlib import Path

import App.config
from App.Extensions import getObject


class GetObjectTests(unittest.TestCase):
    """Testing ..Extensions.getObject()."""

    def setUp(self):
        cfg = App.config.getConfiguration()
        assert not hasattr(cfg, 'extensions')
        cfg.extensions = Path(__file__).parent / 'fixtures'

    def tearDown(self):
        cfg = App.config.getConfiguration()
        del cfg.extensions

    def test_Extensions__getObject__1(self):
        """Check that "getObject" returns the requested function and ...

        that its code object has the path set.
        """
        obj = getObject('getObject', 'f1')
        self.assertIsInstance(obj, types.FunctionType)
        self.assertEqual(obj.__name__, 'f1')
        path = obj()
        self.assertTrue(
            path.endswith(str(Path('App/tests/fixtures/getObject.py'))))

    def test_Extensions__getObject__2(self):
        """It raises a SyntaxError if necessary."""
        try:
            getObject('error', 'f1')
        except SyntaxError as e:
            self.assertEqual(str(e), 'invalid syntax (error.py, line 2)')
