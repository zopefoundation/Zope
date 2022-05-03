from ..engine import _compile_zt_expr
from ..engine import _zt_expr_registry
from ..Expressions import getEngine
from . import testHTMLTests


class ZopeTalesExpressionTests(testHTMLTests.HTMLTests):
    """The tests (currently) always use ``zope.tales`` expressions.
    The tests in this class ensure that the ``_zt_expr_registry``
    is cleared at the start and end of each test.
    """
    def setUp(self):
        super().setUp()
        _zt_expr_registry.clear()

    def tearDown(self):
        _zt_expr_registry.clear()
        super().tearDown()

    def testCaching(self):
        self.test_2()  # fill the cache
        self.assertTrue(_zt_expr_registry)
        key = list(_zt_expr_registry)[0]
        czt = _zt_expr_registry[key]
        zt = _compile_zt_expr(*key[1:], engine=getEngine())
        self.assertIs(czt, _zt_expr_registry[key])
        self.assertIs(zt, _zt_expr_registry[key])

    def testEvaluationTimeCompilation(self):
        self.test_2()  # expressions have been compiled at compilation time
        _zt_expr_registry.clear()
        self.test_2()  # force compilation at evaluation time
