"""Virtual Host Monster regression tests.

These tests mainly verify that OFS.Traversable.absolute_url() 
works correctly in a VHM environment.

Also see http://zope.org/Collectors/Zope/809

Note: Tests require Zope >= 2.7

$Id: testVirtualHostMonster.py,v 1.2 2003/12/10 17:52:47 evan Exp $
"""

from Testing.makerequest import makerequest

import Zope
Zope.startup()

import unittest


class VHMRegressions(unittest.TestCase):

    def setUp(self):
        get_transaction().begin()
        self.app = makerequest(Zope.app())
        try:
            self.app.manage_addProduct['SiteAccess'].manage_addVirtualHostMonster('VHM')
            self.app.manage_addFolder('folder')
            self.app.folder.manage_addDTMLMethod('doc', '')
            self.app.REQUEST.set('PARENTS', [self.app])
            self.traverse = self.app.REQUEST.traverse
        except:
            self.tearDown()

    def tearDown(self):
        get_transaction().abort()
        self.app._p_jar.close()

    def testAbsoluteUrl(self):
        m = self.app.folder.doc.absolute_url
        self.assertEqual(m(), 'http://foo/folder/doc')

    def testAbsoluteUrlPath(self):
        m = self.app.folder.doc.absolute_url_path
        self.assertEqual(m(), '/folder/doc')

    def testVirtualUrlPath(self):
        m = self.app.folder.doc.absolute_url
        self.assertEqual(m(relative=1), 'folder/doc')
        m = self.app.folder.doc.virtual_url_path
        self.assertEqual(m(), 'folder/doc')

    def testPhysicalPath(self):
        m = self.app.folder.doc.getPhysicalPath
        self.assertEqual(m(), ('', 'folder', 'doc'))

def gen_cases():
    for vbase, ubase in (
        ('', 'http://foo'),
        ('/VirtualHostBase/http/example.com:80', 'http://example.com'),
        ):
        yield vbase, '', '', 'folder/doc', ubase
        for vr, _vh, p in (
            ('folder', '', 'doc'),
            ('folder', 'foo', 'doc'),
            ('', 'foo', 'folder/doc'),
            ):
            vparts = [vbase, vr, 'VirtualHostRoot']
            if not vr:
                del vparts[1]
            if _vh:
                vparts.append('_vh_' + _vh)
            yield '/'.join(vparts), vr, _vh, p, ubase

for i, (vaddr, vr, _vh, p, ubase) in enumerate(gen_cases()):
    def test(self):
        ob = self.traverse('%s/%s/' % (vaddr, p))
        vhp = '/' + '/'.join([x for x in _vh, p if x])
        self.assertEqual(ob.absolute_url(), ubase + vhp)
        self.assertEqual(ob.absolute_url_path(), vhp)
        self.assertEqual(ob.absolute_url(relative=1), p)
        self.assertEqual(ob.virtual_url_path(), p)
        self.assertEqual(ob.getPhysicalPath(), ('', 'folder', 'doc'))

        app = ob.aq_parent.aq_parent
        self.assertEqual(app.absolute_url(), ubase + '/' + _vh)
        self.assertEqual(app.absolute_url_path(), '/' + _vh)
        self.assertEqual(app.absolute_url(relative=1), '')
        self.assertEqual(app.virtual_url_path(), '')

    setattr(VHMRegressions, 'testTraverse%s' % i, test)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(VHMRegressions))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

