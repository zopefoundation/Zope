import ST
import DocumentClass
import ClassicDocumentClass
import unittest
import StructuredText
import HTMLClass

from string import join

"""
This tester first ensures that all regression files
can at least parse all files.
Secondly, the tester will compare the output between
StructuredText and ClassicDocumentClass->HTMLClass
to help ensure backwards compatability.
"""

class StructuredTextIndexTestCase(unittest.TestCase):
    def setUp(self):
        myfile  = open("regressions/index.stx","r")
        lines   = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = lines
    def runTest(self):
        assert StructuredText.StructuredText(self.raw_text), \
            'StructuredText failed on index'

class StructuredTextAcquisitionTestCase(unittest.TestCase):
    def setUp(self):
        myfile  = open("regressions/Acquisition.stx","r")
        lines   = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = lines
    def runTest(self):
        assert StructuredText.StructuredText(self.raw_text), \
            'StructuredText failed on Acquisition'

class StructuredTextExtensionClassTestCase(unittest.TestCase):
    def setUp(self):
        myfile  = open("regressions/index.stx","r")
        lines   = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = lines
    def runTest(self):
        assert StructuredText.StructuredText(self.raw_text), \
            'StructuredText failed on ExtensionClass'

class StructuredTextMultiMappingTestCase(unittest.TestCase):
    def setUp(self):
        myfile  = open("regressions/MultiMapping.stx","r")
        lines   = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = lines
    def runTest(self):
        assert StructuredText.StructuredText(self.raw_text), \
            'StructuredText failed on MultiMapping'

class StructuredTextExamplesTestCase(unittest.TestCase):
    def setUp(self):
        myfile  = open("regressions/examples.stx","r")
        lines   = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = lines
    def runTest(self):
        assert StructuredText.StructuredText(self.raw_text), \
            'StructuredText failed on examples'
        
class STNGIndexTestCase(unittest.TestCase):
    def setUp(self):
        myfile  = open("regressions/index.stx","r")
        lines   = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = lines
    def runTest(self):
        assert ST.StructuredText(self.raw_text), \
            'StructuredTextNG failed on index'

class STNGAcquisitionTestCase(unittest.TestCase):
    def setUp(self):
        myfile  = open("regressions/Acquisition.stx","r")
        lines   = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = lines
    def runTest(self):
        assert ST.StructuredText(self.raw_text), \
            'StructuredTextNG failed on Acquisition'

class STNGExtensionClassTestCase(unittest.TestCase):
    def setUp(self):
        myfile  = open("regressions/ExtensionClass.stx","r")
        lines   = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = lines
    def runTest(self):
        assert ST.StructuredText(self.raw_text), \
            'StructuredTextNG failed on ExtensionClass'

class STNGMultiMappingTestCase(unittest.TestCase):
    def setUp(self):
        myfile  = open("regressions/MultiMapping.stx","r")
        lines   = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = lines
    def runTest(self):
        assert ST.StructuredText(self.raw_text), \
            'StructuredTextNG failed on MultiMapping'

class STNGExamplesTestCase(unittest.TestCase):
    def setUp(self):
        myfile  = open("regressions/examples.stx","r")
        lines   = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = lines
    def runTest(self):
        assert ST.StructuredText(self.raw_text), \
            'StructuredTextNG failed on examples'
    
class DocumentClassIndexTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = DocumentClass.DocumentClass()
        myfile      = open("regressions/index.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = ST.StructuredText(lines)
    def runTest(self):
        assert self.Doc(self.text), \
            'DocumentClass failed on index'
    
class DocumentClassAcquisitionTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = DocumentClass.DocumentClass()
        myfile      = open("regressions/Acquisition.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = ST.StructuredText(lines)
    def runTest(self):
        assert self.Doc(self.text), \
            'DocumentClass failed on Acquisition'
    
class DocumentClassExtensionClassTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = DocumentClass.DocumentClass()
        myfile      = open("regressions/ExtensionClass.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = ST.StructuredText(lines)
    def runTest(self):
        assert self.Doc(self.text), \
            'DocumentClass failed on ExtensionClass'
    
class DocumentClassMultiMappingTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = DocumentClass.DocumentClass()
        myfile      = open("regressions/MultiMapping.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = ST.StructuredText(lines)
    def runTest(self):
        assert self.Doc(self.text), \
            'DocumentClass failed on MultiMapping'
    
class DocumentClassExamplesTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = DocumentClass.DocumentClass()
        myfile      = open("regressions/examples.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = ST.StructuredText(lines)
    def runTest(self):
        assert self.Doc(self.text), \
            'DocumentClass failed on examples'

class ClassicDocumentClassIndexTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = ClassicDocumentClass.DocumentClass()
        myfile      = open("regressions/index.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = ST.StructuredText(lines)
    def runTest(self):
        assert self.Doc(self.text), \
            'DocumentClass failed on index'
    
class ClassicDocumentClassAcquisitionTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = ClassicDocumentClass.DocumentClass()
        myfile      = open("regressions/Acquisition.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = ST.StructuredText(lines)
    def runTest(self):
        assert self.Doc(self.text), \
            'DocumentClass failed on Acquisition'
    
class ClassicDocumentClassExtensionClassTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = ClassicDocumentClass.DocumentClass()
        myfile      = open("regressions/ExtensionClass.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = ST.StructuredText(lines)
    def runTest(self):
        assert self.Doc(self.text), \
            'DocumentClass failed on ExtensionClass'
    
class ClassicDocumentClassMultiMappingTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = ClassicDocumentClass.DocumentClass()
        myfile      = open("regressions/MultiMapping.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = ST.StructuredText(lines)
    def runTest(self):
        assert self.Doc(self.text), \
            'DocumentClass failed on MultiMapping'
    
class ClassicDocumentClassExamplesTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = ClassicDocumentClass.DocumentClass()
        myfile      = open("regressions/examples.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = ST.StructuredText(lines)
    def runTest(self):
        assert self.Doc(self.text), \
            'DocumentClass failed on examples'

class ClassicHtmlIndexTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = ClassicDocumentClass.DocumentClass()
        self.HTML   = HTMLClass.HTMLClass()
        myfile      = open("regressions/index.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = self.Doc(ST.StructuredText(lines))
    def runTest(self):
        assert self.HTML(self.text),\
            'HTML failed on classic index'

class ClassicHtmlAcquisitionTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = ClassicDocumentClass.DocumentClass()
        self.HTML   = HTMLClass.HTMLClass()
        myfile      = open("regressions/Acquisition.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = self.Doc(ST.StructuredText(lines))
    def runTest(self):
        assert self.HTML(self.text),\
            'HTML failed on classic Acquisition '

class ClassicHtmlExtensionClassTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = ClassicDocumentClass.DocumentClass()
        self.HTML   = HTMLClass.HTMLClass()
        myfile      = open("regressions/ExtensionClass.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = self.Doc(ST.StructuredText(lines))
    def runTest(self):
        assert self.HTML(self.text),\
            'HTML failed on classic ExtensionClass'

class ClassicHtmlMultiMappingTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = ClassicDocumentClass.DocumentClass()
        self.HTML   = HTMLClass.HTMLClass()
        myfile      = open("regressions/MultiMapping.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = self.Doc(ST.StructuredText(lines))
    def runTest(self):
        assert self.HTML(self.text),\
            'MultiMapping'

class ClassicHtmlExamplesTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = ClassicDocumentClass.DocumentClass()
        self.HTML   = HTMLClass.HTMLClass()
        myfile      = open("regressions/examples.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = self.Doc(ST.StructuredText(lines))
    def runTest(self):
        assert self.HTML(self.text),\
            'HTML failed on classic examples'
    

class HtmlIndexTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = DocumentClass.DocumentClass()
        self.HTML   = HTMLClass.HTMLClass()
        myfile      = open("regressions/index.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = self.Doc(ST.StructuredText(lines))
    def runTest(self):
        assert self.HTML(self.text),\
            'HTML failed on classic index'

class HtmlAcquisitionTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = DocumentClass.DocumentClass()
        self.HTML   = HTMLClass.HTMLClass()
        myfile      = open("regressions/Acquisition.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = self.Doc(ST.StructuredText(lines))
    def runTest(self):
        assert self.HTML(self.text),\
            'HTML failed on classic Acquisition '

class HtmlExtensionClassTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = DocumentClass.DocumentClass()
        self.HTML   = HTMLClass.HTMLClass()
        myfile      = open("regressions/ExtensionClass.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = self.Doc(ST.StructuredText(lines))
    def runTest(self):
        assert self.HTML(self.text),\
            'HTML failed on classic ExtensionClass'

class HtmlMultiMappingTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = DocumentClass.DocumentClass()
        self.HTML   = HTMLClass.HTMLClass()
        myfile      = open("regressions/MultiMapping.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = self.Doc(ST.StructuredText(lines))
    def runTest(self):
        assert self.HTML(self.text),\
            'MultiMapping'

class HtmlExamplesTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc    = DocumentClass.DocumentClass()
        self.HTML   = HTMLClass.HTMLClass()
        myfile      = open("regressions/examples.stx","r")
        lines       = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.text = self.Doc(ST.StructuredText(lines))
    def runTest(self):
        assert self.HTML(self.text),\
            'HTML failed on classic examples'
    
class IndexRegressionTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc            = ClassicDocumentClass.DocumentClass()
        self.HTML           = HTMLClass.HTMLClass()
        self.ST = StructuredText.StructuredText
        myfile = open("regressions/index.stx","r")
        lines = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = self.Doc(lines)
    
    def runTest(self):
        assert self.HTML(self.Doc(self.ST(self.raw_text))) == self.StructuredText(raw_text), \
            'StructuredText and ClassicDocumentClass do not match on index.stx'

class AcquisitionRegressionTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc            = ClassicDocumentClass.DocumentClass()
        self.HTML           = HTMLClass.HTMLClass()
        self.ST = StructuredText.StructuredText
        myfile = open("regressions/Acquisition.stx","r")
        lines = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = self.Doc(lines)
    def runTest(self):
        assert self.HTML(self.Doc(self.ST(self.raw_text))) == self.StructuredText(raw_text), \
            'StructuredText and ClassicDocumentClass do not match on Acquisition.stx'

class ExtensionClassRegressionTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc            = ClassicDocumentClass.DocumentClass()
        self.HTML           = HTMLClass.HTMLClass()
        self.ST = StructuredText.StructuredText
        myfile = open("regressions/ExtensionClass.stx","r")
        lines = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = self.Doc(lines)
    def runTest(self):
        assert self.HTML(self.Doc(self.ST(self.raw_text))) == self.StructuredText(raw_text), \
            'StructuredText and ClassicDocumentClass do not match on ExtensionClass.stx'

class MultiMappingRegressionTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc            = ClassicDocumentClass.DocumentClass()
        self.HTML           = HTMLClass.HTMLClass()
        self.ST = StructuredText.StructuredText
        myfile = open("regressions/MultiMapping.stx","r")
        lines = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = self.Doc(lines)
    def runTest(self):
        assert self.HTML(self.Doc(self.ST(self.raw_text))) == self.StructuredText(raw_text), \
            'StructuredText and ClassicDocumentClass do not match on MultiMapping.stx'

class ExamplesRegressionTestCase(unittest.TestCase):
    def setUp(self):
        self.Doc            = ClassicDocumentClass.DocumentClass()
        self.ST             = ST.StructuredText
        self.HTML           = HTMLClass.HTMLClass()
        self.ST = StructuredText.StructuredText
        myfile = open("regressions/examples.stx","r")
        lines = myfile.readlines()
        myfile.close()
        lines = join(lines)
        self.raw_text = self.Doc(lines)
    
    def runTest(self):
        assert self.HTML(self.Doc(self.ST(self.raw_text))) == self.StructuredText(raw_text), \
            'StructuredText and ClassicDocumentClass do not match on examples.stx'

ClassicHTMLTestSuite            = unittest.TestSuite()
HTMLTestSuite                   = unittest.TestSuite()
ClassicDocumentClassTestSuite   = unittest.TestSuite()
DocumentClassTestSuite          = unittest.TestSuite()
STNGTestSuite                   = unittest.TestSuite()
StructuredTextTestSuite         = unittest.TestSuite()
RegressionTestSuite             = unittest.TestSuite()

ClassicHTMLTestSuite.addTest(ClassicHtmlIndexTestCase("runTest"))
ClassicHTMLTestSuite.addTest(ClassicHtmlAcquisitionTestCase("runTest"))
ClassicHTMLTestSuite.addTest(ClassicHtmlExtensionClassTestCase("runTest"))
ClassicHTMLTestSuite.addTest(ClassicHtmlMultiMappingTestCase("runTest"))
ClassicHTMLTestSuite.addTest(ClassicHtmlExamplesTestCase("runTest"))

HTMLTestSuite.addTest(HtmlIndexTestCase("runTest"))
HTMLTestSuite.addTest(HtmlAcquisitionTestCase("runTest"))
HTMLTestSuite.addTest(HtmlExtensionClassTestCase("runTest"))
HTMLTestSuite.addTest(HtmlMultiMappingTestCase("runTest"))
HTMLTestSuite.addTest(HtmlExamplesTestCase("runTest"))

ClassicDocumentClassTestSuite.addTest(ClassicDocumentClassIndexTestCase("runTest"))
ClassicDocumentClassTestSuite.addTest(ClassicDocumentClassAcquisitionTestCase("runTest"))
ClassicDocumentClassTestSuite.addTest(ClassicDocumentClassExtensionClassTestCase("runTest"))
ClassicDocumentClassTestSuite.addTest(ClassicDocumentClassMultiMappingTestCase("runTest"))
ClassicDocumentClassTestSuite.addTest(ClassicDocumentClassExamplesTestCase("runTest"))

DocumentClassTestSuite.addTest(DocumentClassIndexTestCase("runTest"))
DocumentClassTestSuite.addTest(DocumentClassAcquisitionTestCase("runTest"))
DocumentClassTestSuite.addTest(DocumentClassExtensionClassTestCase("runTest"))
DocumentClassTestSuite.addTest(DocumentClassMultiMappingTestCase("runTest"))
DocumentClassTestSuite.addTest(DocumentClassExamplesTestCase("runTest"))

STNGTestSuite.addTest(STNGIndexTestCase("runTest"))
STNGTestSuite.addTest(STNGAcquisitionTestCase("runTest"))
STNGTestSuite.addTest(STNGExtensionClassTestCase("runTest"))
STNGTestSuite.addTest(STNGMultiMappingTestCase("runTest"))
STNGTestSuite.addTest(STNGExamplesTestCase("runTest"))

StructuredTextTestSuite.addTest(StructuredTextIndexTestCase("runTest"))
StructuredTextTestSuite.addTest(StructuredTextAcquisitionTestCase("runTest"))
StructuredTextTestSuite.addTest(StructuredTextExtensionClassTestCase("runTest"))
StructuredTextTestSuite.addTest(StructuredTextMultiMappingTestCase("runTest"))
StructuredTextTestSuite.addTest(StructuredTextExamplesTestCase("runTest"))

RegressionTestSuite.addTest(IndexRegressionTestCase("runTest"))
RegressionTestSuite.addTest(AcquisitionRegressionTestCase("runTest"))
RegressionTestSuite.addTest(ExtensionClassRegressionTestCase("runTest"))
RegressionTestSuite.addTest(MultiMappingRegressionTestCase("runTest"))
RegressionTestSuite.addTest(ExamplesRegressionTestCase("runTest"))

runner = unittest.TextTestRunner()

runner.run(ClassicHTMLTestSuite)
runner.run(HTMLTestSuite)

runner.run(ClassicDocumentClassTestSuite)
runner.run(DocumentClassTestSuite)
runner.run(STNGTestSuite)
runner.run(StructuredTextTestSuite)
#runner.run(RegressionTestSuite)
