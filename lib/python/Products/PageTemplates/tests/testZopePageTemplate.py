# -*- encoding: iso-8859-15 -*-

"""ZopePageTemplate regression tests.

Ensures that adding a page template works correctly.

Note: Tests require Zope >= 2.7

"""

import unittest
import Zope2
import transaction
import zope.component.testing
from zope.traversing.adapters import DefaultTraversable
from Testing.makerequest import makerequest
from Testing.ZopeTestCase import ZopeTestCase, installProduct
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate, manage_addPageTemplate


ascii_str = '<html><body>hello world</body></html>'
iso885915_str = '<html><body>üöäÜÖÄß</body></html>'
utf8_str = unicode(iso885915_str, 'iso-8859-15').encode('utf-8')

xml_template = '''<?xml vesion="1.0" encoding="%s"?>
<foo>
üöäÜÖÄß
</foo>
'''

xml_iso_8859_15 = xml_template % 'iso-8859-15'
xml_utf8 = unicode(xml_template, 'iso-8859-15').encode('utf-8') % 'utf-8'

html_template_w_header = '''
<html>
    <head>
        <META http-equiv="content-type" content="text/html; charset=%s">
    </hed>
    <body>
    test üöäÜÖÄß
    </body>
</html>
'''

html_iso_8859_15_w_header = html_template_w_header % 'iso-8859-15'
html_utf8_w_header = unicode(html_template_w_header, 'iso-8859-15').encode('utf-8') % 'utf-8'

html_template_wo_header = '''
<html>
    <head>
        <META http-equiv="content-type" content="text/html; charset=%s">
    </hed>
    <body>
    test üöäÜÖÄß
    </body>
</html>
'''

html_iso_8859_15_wo_header = html_template_wo_header % 'iso-8859-15'
html_utf8_wo_header = unicode(html_template_wo_header, 'iso-8859-15').encode('utf-8') % 'utf-8'


installProduct('PageTemplates')


class ZopePageTemplateFileTests(ZopeTestCase):

    def testPT_RenderWithAscii(self):
        manage_addPageTemplate(self.app, 'test', text=ascii_str, encoding='ascii')
        zpt = self.app['test']
        result = zpt.pt_render()
        # use startswith() because the renderer appends a trailing \n
        self.assertEqual(result.startswith(ascii_str), True)

    def testPT_RenderWithISO885915(self):
        manage_addPageTemplate(self.app, 'test', text=iso885915_str, encoding='iso-8859-15')
        zpt = self.app['test']
        result = zpt.pt_render()
        # use startswith() because the renderer appends a trailing \n
        self.assertEqual(result.startswith(iso885915_str), True)

    def testPT_RenderWithUTF8(self):
        manage_addPageTemplate(self.app, 'test', text=utf8_str, encoding='utf-8')
        zpt = self.app['test']
        result = zpt.pt_render()
        # use startswith() because the renderer appends a trailing \n
        self.assertEqual(result.startswith(utf8_str), True)

    def _createZPT(self):
        manage_addPageTemplate(self.app, 'test', text=utf8_str, encoding='utf-8')
        zpt = self.app['test']
        return zpt

    def _makePUTRequest(self, body):
        return {'BODY' : body}

    def _put(self, text):
        zpt = self._createZPT()
        REQUEST = self.app.REQUEST
        REQUEST.set('BODY', text)
        zpt.PUT(REQUEST, REQUEST.RESPONSE)
        return zpt.output_encoding

    def testPutHTMLIso8859_15WithCharsetInfo(self):
        self.assertEqual(self._put(html_iso_8859_15_w_header), 'iso-8859-15')

    def testPutHTMLUTF8_WithCharsetInfo(self):
        self.assertEqual(self._put(html_utf8_w_header), 'utf-8')

    def testPutXMLIso8859_15(self):
        """ XML: use always UTF-8 als output encoding """
        self.assertEqual(self._put(xml_iso_8859_15), 'utf-8')

    def testPutXMLUTF8(self):
        """ XML: use always UTF-8 als output encoding """
        self.assertEqual(self._put(xml_utf8), 'utf-8')

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
        default_text = open(pt._default_content_fn).read()
        self.assertEqual(pt.title, '')
        self.assertEqual(pt.document_src().strip(), default_text.strip())

    def testAddWithRequest(self):
        # Test manage_add with file
        request = self.app.REQUEST
        request.form['file'] = DummyFileUpload(filename='some file',
                                               data=self.text,
                                               content_type='text/html')
        self._addPT('pt1', REQUEST=request)
        # no object is returned when REQUEST is passed.
        pt = self.app.pt1
        self.assertEqual(pt.document_src(), self.text)

    def testAddWithRequestButNoFile(self):
        # Collector #596: manage_add with text but no file
        request = self.app.REQUEST
        self._addPT('pt1', text=self.text, REQUEST=request)
        # no object is returned when REQUEST is passed.
        pt = self.app.pt1
        self.assertEqual(pt.document_src(), self.text)

    def test_BBB_for_strict_attribute(self):
        # Collector 2213:  old templates don't have 'strict' attribute.
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        zpt = ZopePageTemplate('issue_2213')
        del zpt.strict  # simulate old templates
        self.assertEqual(zpt.strict, True)


class ZPTMacros(zope.component.testing.PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(ZPTMacros, self).setUp()
        zope.component.provideAdapter(DefaultTraversable, (None,))

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

    def tearDown(self):
        super(ZPTMacros, self).tearDown()

        transaction.abort()
        self.app._p_jar.close()

    def testMacroExpansion(self):
        request = self.app.REQUEST        
        self._addPT('pt1', text=self.text, REQUEST=request)
        pt = self.app.pt1
        self.assertEqual(pt(), self.result)

    def testPtErrors(self):
        request = self.app.REQUEST        
        self._addPT('pt1', text=self.text, REQUEST=request)
        pt = self.app.pt1
        pt.pt_render(source=True)
        self.assertEqual(pt.pt_errors(), None)

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
    suite.addTests(unittest.makeSuite(ZopePageTemplateFileTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

