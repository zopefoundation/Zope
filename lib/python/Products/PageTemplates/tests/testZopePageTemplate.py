"""ZopePageTemplate regression tests.

Ensures that adding a page template works correctly.

Note: Tests require Zope >= 2.7

"""


import unittest
import Zope2
import transaction

from Testing.makerequest import makerequest
from Products.PageTemplates.ZopePageTemplate import _default_content_fn

class ZPTRegressions(unittest.TestCase):

    def setUp(self):
        transaction.begin()
        self.app = makerequest(Zope2.app())
        f = self.app.manage_addProduct['PageTemplates'].manage_addPageTemplate
        self._addPT = f
        self.title = 'title of page template'
        self.text = 'text of page template'

    def tearDown(self):
        transaction.abort()
        self.app._p_jar.close()

    def testAddWithParams(self):
        pt = self._addPT('pt1', title=self.title, text=self.text)
        self.assertEqual(pt.title, self.title)
        self.assertEqual(pt.document_src(), self.text)

    def testAddWithoutParams(self):
        pt = self._addPT('pt1')
        default_text = open(_default_content_fn).read()
        self.assertEqual(pt.title, '')
        self.assertEqual(pt.document_src().strip(), default_text.strip())

    def testAddWithRequest(self):
        """Test manage_add with file"""
        request = self.app.REQUEST
        request.form['file'] = DummyFileUpload(filename='some file',
                                               data=self.text,
                                               content_type='text/html')
        self._addPT('pt1', REQUEST=request)
        # no object is returned when REQUEST is passed.
        pt = self.app.pt1
        self.assertEqual(pt.document_src(), self.text)

    def testAddWithRequestButNoFile(self):
        """Collector #596: manage_add with text but no file"""
        request = self.app.REQUEST
        self._addPT('pt1', text=self.text, REQUEST=request)
        # no object is returned when REQUEST is passed.
        pt = self.app.pt1
        self.assertEqual(pt.document_src(), self.text)

class ZPTMacros(unittest.TestCase):
    def setUp(self):
        transaction.begin()
        self.app = makerequest(Zope2.app())
        f = self.app.manage_addProduct['PageTemplates'].manage_addPageTemplate
        self._addPT = f
        self.title = 'title of page template'
        self.text = """
<metal:block use-macro="template/macros/themacro">
  <p metal:fill-slot="theslot">
    This is in the slot
  </p>
</metal:block>
<tal:block condition="nothing">
<div metal:define-macro="themacro">
  <h1>This is the header</h1>
  <p metal:define-slot="theslot">
    This will be replaced
  </p>
</div>
</tal:block>
"""
        self.result = """<div>
  <h1>This is the header</h1>
  <p>
    This is in the slot
  </p>
</div>
"""       

    def testMacroExpansion(self):
        request = self.app.REQUEST        
        self._addPT('pt1', text=self.text, REQUEST=request)
        pt = self.app.pt1
        self.assertEqual(pt(), self.result)

        
class DummyFileUpload:

    def __init__(self, data='', filename='', content_type=''):
        self.data = data
        self.filename = filename
        self.headers = {'content_type': content_type}

    def read(self):
        return self.data

       
def test_suite():
    suite = unittest.makeSuite(ZPTRegressions)
    suite.addTests(unittest.makeSuite(ZPTMacros))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

