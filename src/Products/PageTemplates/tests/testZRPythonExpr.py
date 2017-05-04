""" Unit tests for Products.PageTemplates.ZRPythonExpr
"""

import unittest


class ZRPPythonExprTest(unittest.TestCase):

    def test_call_with_ns_prefer_context_to_here(self):
        from Products.PageTemplates.ZRPythonExpr import call_with_ns
        context = ['context']
        here = ['here']
        request = {'request': 1}
        names = {'context': context, 'here': here, 'request': request}
        result = call_with_ns(lambda td: td.this, names)
        self.assertTrue(result is context, result)

    def test_call_with_ns_no_context_or_here(self):
        from Products.PageTemplates.ZRPythonExpr import call_with_ns
        request = {'request': 1}
        names = {'request': request}
        result = call_with_ns(lambda td: td.this, names)
        self.assertTrue(result is None, result)

    def test_call_with_ns_no_request(self):
        from Products.PageTemplates.ZRPythonExpr import call_with_ns
        context = ['context']
        here = ['here']
        names = {'context': context, 'here': here}

        def _find_request(td):
            ns = td._pop()              # peel off 'ns'
            instance_dict = td._pop()   # peel off InstanceDict
            request = td._pop()
            td._push(request)
            td._push(instance_dict)
            td._push(ns)
            return request

        result = call_with_ns(_find_request, names)
        self.assertEqual(result, {})

    def test_call_with_request_preserves_tainting(self):
        from Products.PageTemplates.ZRPythonExpr import call_with_ns

        class Request(dict):
            def taintWrapper(self):
                return {'tainted': 'found'}

        context = ['context']
        here = ['here']
        names = {'context': context, 'here': here, 'request': Request()}

        found = call_with_ns(lambda td: td['tainted'], names)
        self.assertEqual(found, 'found')
