from StructuredText import ST
from StructuredText import DocumentClass
from StructuredText import ClassicDocumentClass
from StructuredText import StructuredText
from StructuredText import HTMLClass
import sys, os, unittest
execfile(os.path.join(sys.path[0],'framework.py'))

"""
This tester first ensures that all regression files
can at least parse all files.
Secondly, the tester will compare the output between
StructuredText and ClassicDocumentClass->HTMLClass
to help ensure backwards compatability.
"""

package_dir = os.path.split(ST.__file__)[0]
regressions=os.path.join(package_dir, 'regressions')

files = ['index.stx','Acquisition.stx','ExtensionClass.stx',
        'MultiMapping.stx','examples.stx']


def readFile(dirname,fname):

    myfile  = open(os.path.join(dirname, fname),"r")
    lines   = myfile.readlines()
    myfile.close()
    return  ''.join(lines)


class StructuredTextTests(unittest.TestCase):

    def testStructuredText(self):
        """ testing StructuredText """

        for f in files:
            raw_text = readFile(regressions,f)
            assert StructuredText.StructuredText(raw_text),\
                'StructuredText failed on %s' % f

    def testStructuredTextNG(self):
        """ testing StructuredTextNG """

        for f in files:
            raw_text = readFile(regressions,f)
            assert ST.StructuredText(raw_text),\
                'StructuredText failed on %s' % f


    def testDocumentClass(self):
        """ testing DocumentClass"""

        for f in files:
            Doc = DocumentClass.DocumentClass()
            raw_text = readFile(regressions,f)
            text = ST.StructuredText(raw_text)
            assert Doc(text),\
                'DocumentClass failed on %s' % f

    def testClassicDocumentClass(self):
        """ testing ClassicDocumentClass"""

        for f in files:
            Doc = ClassicDocumentClass.DocumentClass()
            raw_text = readFile(regressions,f)
            text = ST.StructuredText(raw_text)
            assert Doc(text),\
                'ClassicDocumentClass failed on %s' % f

    def testClassicHTMLDocumentClass(self):
        """ testing HTML ClassicDocumentClass"""

        for f in files:
            Doc = ClassicDocumentClass.DocumentClass()
            HTML = HTMLClass.HTMLClass()
            raw_text = readFile(regressions,f)
            text = Doc(ST.StructuredText(raw_text))
            assert HTML(text),\
                'HTML ClassicDocumentClass failed on %s' % f


#    def testRegressionsTests(self)
#        """ there should be a regression tests that compares 
#             generated HTML against the reference HTML files.
#             This test is commented in the 2.4 branch because
#             of the change from ST to STXNG and the changed 
#             HTML generation (HTML references files are no longer
#             valid for STXNG)

framework()
