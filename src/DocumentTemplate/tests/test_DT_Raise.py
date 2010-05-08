import unittest

class Test_Raise(unittest.TestCase):

    def _getTargetClass(self):
        from DocumentTemplate.DT_Raise import Raise
        return Raise

    def _makeOne(self, type=None, expr=None):
        args = []
        if type is not None:
            args.append('type="%s"' % type)
        if expr is not None:
            args.append('expr="%s"' % expr)
        blocks = [('raise', ' '.join(args), DummySection())]
        return self._getTargetClass()(blocks)

    def test_ctor_w_type(self):
        raiser = self._makeOne(type='Redirect')
        self.assertEqual(raiser.__name__, 'Redirect')
        self.assertEqual(raiser.expr, None)

    def test_ctor_w_expr(self):
        raiser = self._makeOne(expr='SyntaxError')
        self.assertEqual(raiser.__name__, 'SyntaxError')
        self.assertEqual(raiser.expr.expr, 'SyntaxError')

    def test_render_w_type_builtin_exception(self):
        from DocumentTemplate.DT_Util import TemplateDict
        raiser = self._makeOne(type='SyntaxError')
        self.assertRaises(SyntaxError, raiser.render, TemplateDict())

    def test_render_w_type_zExceptions_exception(self):
        from DocumentTemplate.DT_Util import TemplateDict
        from zExceptions import Redirect
        raiser = self._makeOne(type='Redirect')
        self.assertRaises(Redirect, raiser.render, TemplateDict())

    def test_render_w_type_nonesuch(self):
        from DocumentTemplate.DT_Util import TemplateDict
        raiser = self._makeOne(type='NonesuchError')
        self.assertRaises(RuntimeError, raiser.render, TemplateDict())

    def test_render_w_expr_builtin_exception(self):
        from DocumentTemplate.DT_Util import TemplateDict
        raiser = self._makeOne(expr='SyntaxError')
        self.assertRaises(SyntaxError, raiser.render, TemplateDict())

    def test_render_w_expr_zExceptions_exception(self):
        from DocumentTemplate.DT_Util import TemplateDict
        from zExceptions import Redirect
        raiser = self._makeOne(expr='Redirect')
        self.assertRaises(Redirect, raiser.render, TemplateDict())

    def test_render_w_expr_nonesuch(self):
        from DocumentTemplate.DT_Raise import InvalidErrorTypeExpression
        from DocumentTemplate.DT_Util import TemplateDict
        raiser = self._makeOne(expr='NonesuchError')
        self.assertRaises(InvalidErrorTypeExpression,
                          raiser.render, TemplateDict())

class DummySection:
    blocks = ['dummy']

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Test_Raise),
    ))
