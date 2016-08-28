"""Virtual Host Monster regression tests.

These tests mainly verify that OFS.Traversable.absolute_url()
works correctly in a VHM environment.

Also see http://zope.org/Collectors/Zope/809
"""
import unittest


class VHMRegressions(unittest.TestCase):

    def setUp(self):
        import transaction
        from Testing.makerequest import makerequest
        from Testing.ZopeTestCase.ZopeLite import app
        transaction.begin()
        self.app = makerequest(app())
        if 'virtual_hosting' not in self.app.objectIds():
            # If ZopeLite was imported, we have no default virtual
            # host monster
            from Products.SiteAccess.VirtualHostMonster \
                import manage_addVirtualHostMonster
            manage_addVirtualHostMonster(self.app, 'virtual_hosting')
        self.app.manage_addFolder('folder')
        self.app.folder.manage_addDTMLMethod('doc', '')
        self.app.REQUEST.set('PARENTS', [self.app])
        self.traverse = self.app.REQUEST.traverse

    def tearDown(self):
        import transaction
        transaction.abort()
        self.app._p_jar.close()

    def testAbsoluteUrl(self):
        m = self.app.folder.doc.absolute_url
        self.assertEqual(m(), 'http://nohost/folder/doc')

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

    def test_actual_url_no_VHR_no_doc_w_trailing_slash(self):
        self.traverse('/VirtualHostBase/http/www.mysite.com:80'
                      '/folder/')
        self.assertEqual(self.app.REQUEST['ACTUAL_URL'],
                         'http://www.mysite.com/folder/')

    def test_actual_url_no_VHR_no_doc_no_trailing_slash(self):
        self.traverse('/VirtualHostBase/http/www.mysite.com:80'
                      '/folder')
        self.assertEqual(self.app.REQUEST['ACTUAL_URL'],
                         'http://www.mysite.com/folder')

    def test_actual_url_no_VHR_w_doc_w_trailing_slash(self):
        self.traverse('/VirtualHostBase/http/www.mysite.com:80'
                      '/folder/doc/')
        self.assertEqual(self.app.REQUEST['ACTUAL_URL'],
                         'http://www.mysite.com/folder/doc/')

    def test_actual_url_no_VHR_w_doc_no_trailing_slash(self):
        self.traverse('/VirtualHostBase/http/www.mysite.com:80'
                      '/folder/doc')
        self.assertEqual(self.app.REQUEST['ACTUAL_URL'],
                         'http://www.mysite.com/folder/doc')

    def test_actual_url_w_VHR_w_doc_w_trailing_slash(self):
        self.traverse('/VirtualHostBase/http/www.mysite.com:80'
                      '/folder/VirtualHostRoot/doc/')
        self.assertEqual(self.app.REQUEST['ACTUAL_URL'],
                         'http://www.mysite.com/doc/')

    def test_actual_url_w_VHR_w_doc_no_trailing_slash(self):
        self.traverse('/VirtualHostBase/http/www.mysite.com:80'
                      '/folder/VirtualHostRoot/doc')
        self.assertEqual(self.app.REQUEST['ACTUAL_URL'],
                         'http://www.mysite.com/doc')

    def test_actual_url_w_VHR_no_doc_w_trailing_slash(self):
        self.traverse('/VirtualHostBase/http/www.mysite.com:80'
                      '/folder/VirtualHostRoot/')
        self.assertEqual(self.app.REQUEST['ACTUAL_URL'],
                         'http://www.mysite.com/')

    def test_actual_url_w_VHR_no_doc_no_trailing_slash(self):
        self.traverse('/VirtualHostBase/http/www.mysite.com:80'
                      '/folder/VirtualHostRoot')
        self.assertEqual(self.app.REQUEST['ACTUAL_URL'],
                         'http://www.mysite.com/')


def gen_cases():
    for vbase, ubase in (
            ('', 'http://nohost'),
            ('/VirtualHostBase/http/example.com:80', 'http://example.com')):
        yield vbase, '', '', 'folder/doc', ubase

        for vr, _vh, p in (
                ('folder', '', 'doc'),
                ('folder', 'foo', 'doc'),
                ('', 'foo', 'folder/doc')):
            vparts = [vbase, vr, 'VirtualHostRoot']
            if not vr:
                del vparts[1]
            if _vh:
                vparts.append('_vh_' + _vh)
            yield '/'.join(vparts), vr, _vh, p, ubase


for i, (vaddr, vr, _vh, p, ubase) in enumerate(gen_cases()):
    def test(self, vaddr=vaddr, vr=vr, _vh=_vh, p=p, ubase=ubase):
        ob = self.traverse('%s/%s/' % (vaddr, p))
        sl_vh = (_vh and ('/' + _vh))
        aup = sl_vh + (p and ('/' + p))
        self.assertEqual(ob.absolute_url_path(), aup)
        self.assertEqual(self.app.REQUEST['BASEPATH1'] + '/' + p, aup)
        self.assertEqual(ob.absolute_url(), ubase + aup)
        self.assertEqual(ob.absolute_url(relative=1), p)
        self.assertEqual(ob.virtual_url_path(), p)
        self.assertEqual(ob.getPhysicalPath(), ('', 'folder', 'doc'))

        app = ob.aq_parent.aq_parent
        # The absolute URL doesn't end with a slash
        self.assertEqual(app.absolute_url(), ubase + sl_vh)
        # The absolute URL path always begins with a slash
        self.assertEqual(app.absolute_url_path(), '/' + _vh)
        self.assertEqual(app.absolute_url(relative=1), '')
        self.assertEqual(app.virtual_url_path(), '')

    setattr(VHMRegressions, 'testTraverse%s' % i, test)


class VHMAddingTests(unittest.TestCase):

    def setUp(self):
        from OFS.Folder import Folder
        super(VHMAddingTests, self).setUp()
        self.root = Folder('root')

    def _makeOne(self):
        from Products.SiteAccess.VirtualHostMonster import VirtualHostMonster
        return VirtualHostMonster()

    def test_add_with_existing_vhm(self):
        from Products.SiteAccess.VirtualHostMonster import \
            manage_addVirtualHostMonster
        from zExceptions import BadRequest
        vhm1 = self._makeOne()
        vhm1.manage_addToContainer(self.root)

        vhm2 = self._makeOne()
        self.assertRaises(BadRequest, vhm2.manage_addToContainer, self.root)
        self.assertRaises(BadRequest, manage_addVirtualHostMonster, self.root)

    def test_add_id_collision(self):
        from OFS.Folder import Folder
        from Products.SiteAccess.VirtualHostMonster import \
            manage_addVirtualHostMonster
        from zExceptions import BadRequest
        self.root._setObject('virtual_hosting', Folder('virtual_hosting'))
        vhm1 = self._makeOne()

        self.assertRaises(BadRequest, vhm1.manage_addToContainer, self.root)
        self.assertRaises(BadRequest, manage_addVirtualHostMonster, self.root)

    def test_add_addToContainer(self):
        from ZPublisher.BeforeTraverse import queryBeforeTraverse
        vhm1 = self._makeOne()
        vhm1.manage_addToContainer(self.root)

        self.assertTrue(vhm1.getId() in self.root.objectIds())
        self.assertTrue(queryBeforeTraverse(self.root, vhm1.meta_type))

    def test_add_manage_addVirtualHostMonster(self):
        from Products.SiteAccess.VirtualHostMonster import \
            manage_addVirtualHostMonster
        from Products.SiteAccess.VirtualHostMonster import VirtualHostMonster
        from ZPublisher.BeforeTraverse import queryBeforeTraverse
        manage_addVirtualHostMonster(self.root)

        self.assertTrue(VirtualHostMonster.id in self.root.objectIds())
        hook = queryBeforeTraverse(self.root, VirtualHostMonster.meta_type)
        self.assertTrue(hook)
