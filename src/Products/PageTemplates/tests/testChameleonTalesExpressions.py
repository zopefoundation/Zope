from ..expression import getEngine
from .testHTMLTests import AqPageTemplate
from .testHTMLTests import HTMLTests


class ChameleonAqPageTemplate(AqPageTemplate):
    def pt_getEngine(self):
        return getEngine()


class ChameleonTalesExpressionTests(HTMLTests):
    def setUp(self):
        super(ChameleonTalesExpressionTests, self).setUp()
        # override with templates using chameleon TALES expressions
        self.folder.laf = ChameleonAqPageTemplate()
        self.folder.t = ChameleonAqPageTemplate()

    # override ``PREFIX`` to be able to account for
    #   small differences between ``zope.tales`` and ``chameleon.tales``
    #   expressions (e.g. the ``zope.tales`` ``not`` expression
    #   returns ``int``, that of ``chameleon.tales`` ``bool``
    PREFIX = "CH_"
