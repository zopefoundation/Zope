#! /usr/bin/env python
"""Tests for TALInterpreter."""

import sys
import unittest

from StringIO import StringIO

# BBB 2005/05/01 -- to be changed after 12 months
# ignore deprecation warnings on import for now
import warnings
showwarning = warnings.showwarning
warnings.showwarning = lambda *a, **k: None
# this old import should remain here until the TAL package is
# completely removed, so that API backward compatibility is properly
# tested
from TAL.HTMLTALParser import HTMLTALParser
from TAL.TALInterpreter import TALInterpreter
from TAL.TALGenerator import TALGenerator
from TAL.DummyEngine import DummyEngine
# restore warning machinery
warnings.showwarning = showwarning


page1 = '''<html metal:use-macro="main"><body>
<div metal:fill-slot="body">
page1=<span tal:replace="position:" />
</div>
</body></html>'''

main_template = '''<html metal:define-macro="main"><body>
main_template=<span tal:replace="position:" />
<div metal:define-slot="body" />
main_template=<span tal:replace="position:" />
<div metal:use-macro="foot" />
main_template=<span tal:replace="position:" />
</body></html>'''

footer = '''<div metal:define-macro="foot">
footer=<span tal:replace="position:" />
</div>'''

expected = '''<html><body>
main_template=main_template (2,14)
<div>
page1=page1 (3,6)
</div>
main_template=main_template (4,14)
<div>
footer=footer (2,7)
</div>
main_template=main_template (6,14)
</body></html>'''



class Tests(unittest.TestCase):

    def parse(self, eng, s, fn):
        gen = TALGenerator(expressionCompiler=eng, xml=0, source_file=fn)
        parser = HTMLTALParser(gen)
        parser.parseString(s)
        program, macros = parser.getCode()
        return program, macros

    def testSourcePositions(self):
        """Ensure source file and position are set correctly by TAL"""
        macros = {}
        eng = DummyEngine(macros)
        page1_program, page1_macros = self.parse(eng, page1, 'page1')
        main_template_program, main_template_macros = self.parse(
            eng, main_template, 'main_template')
        footer_program, footer_macros = self.parse(eng, footer, 'footer')

        macros['main'] = main_template_macros['main']
        macros['foot'] = footer_macros['foot']

        stream = StringIO()
        interp = TALInterpreter(page1_program, macros, eng, stream)
        interp()
        self.assertEqual(stream.getvalue().strip(), expected.strip(),
                         stream.getvalue())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Tests))
    return suite

if __name__ == "__main__":
    unittest.main()
