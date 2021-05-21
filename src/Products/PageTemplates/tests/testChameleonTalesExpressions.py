import unittest

from ..expression import getEngine
from . import testHTMLTests


class ChameleonAqPageTemplate(testHTMLTests.AqPageTemplate):
    def pt_getEngine(self):
        return getEngine()


class ChameleonTalesExpressionTests(testHTMLTests.HTMLTests):
    def setUp(self):
        super().setUp()
        # override with templates using chameleon TALES expressions
        self.folder.laf = ChameleonAqPageTemplate()
        self.folder.t = ChameleonAqPageTemplate()

    # override ``PREFIX`` to be able to account for
    #   small differences between ``zope.tales`` and ``chameleon.tales``
    #   expressions (e.g. the ``zope.tales`` ``not`` expression
    #   returns ``int``, that of ``chameleon.tales`` ``bool``
    PREFIX = "CH_"

    @unittest.skip('The test in the base class relies on a Zope context with'
                   ' the "random" module available in expressions')
    def test_underscore_traversal(self):
        pass
