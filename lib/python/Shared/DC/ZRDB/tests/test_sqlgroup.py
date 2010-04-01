##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import unittest

from UserDict import UserDict

def _sql_quote(v):
    return '"%s"' % v

class SQLGroupTests(unittest.TestCase):

    def _getTargetClass(self):
        from Shared.DC.ZRDB.sqlgroup import SQLGroup
        return SQLGroup

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_ctor_empty_args(self):
        group = self._makeOne([('sqlgroup', '', None)])
        self.assertEqual(group.__name__, 'sqlgroup ')
        self.failIf(group.required)
        self.failIf(group.where)
        self.failIf(group.set)
        self.failIf(group.noparens)

    def test_ctor_required(self):
        group = self._makeOne([('sqlgroup', 'required', None)])
        self.assertEqual(group.__name__, 'sqlgroup required')
        self.failUnless(group.required)
        self.failIf(group.where)
        self.failIf(group.set)
        self.failIf(group.noparens)

    def test_ctor_where(self):
        group = self._makeOne([('sqlgroup', 'where', None)])
        self.assertEqual(group.__name__, 'sqlgroup where')
        self.failIf(group.required)
        self.failUnless(group.where)
        self.failIf(group.set)
        self.failIf(group.noparens)

    def test_ctor_noparens(self):
        group = self._makeOne([('sqlgroup', 'noparens', None)])
        self.assertEqual(group.__name__, 'sqlgroup noparens')
        self.failIf(group.required)
        self.failIf(group.where)
        self.failIf(group.set)
        self.failUnless(group.noparens)

    def test_ctor_set(self):
        group = self._makeOne([('sqlgroup', 'set', None)])
        self.assertEqual(group.__name__, 'sqlgroup set')
        self.failIf(group.required)
        self.failIf(group.where)
        self.failUnless(group.set)
        self.failIf(group.noparens)

    def test_render_empty_optional(self):
        group = self._makeOne([('sqlgroup', '', lambda x, y:'')])
        md = {}
        self.assertEqual(group.render(md), '')

    def test_render_empty_optional_where(self):
        group = self._makeOne([('sqlgroup', 'where', lambda x, y:'')])
        md = {}
        self.assertEqual(group.render(md), '')

    def test_render_empty_optional_set(self):
        group = self._makeOne([('sqlgroup', 'set', lambda x, y:'')])
        md = {}
        self.assertEqual(group.render(md), '')

    def test_render_empty_required_raises_ValueError(self):
        group = self._makeOne([('sqlgroup', 'required', lambda x, y:'')])
        md = {}
        self.assertRaises(ValueError, group.render, md)

    def test_render_one_block(self):
        group = self._makeOne([('sqlgroup', '', lambda x, y:'abc'),
                              ])
        md = {}
        rendered = group.render(md)
        rendered = ''.join(rendered.split('\n'))
        self.assertEqual(rendered, 'abc')

    def test_render_one_block_where(self):
        group = self._makeOne([('sqlgroup', 'where', lambda x, y:'abc'),
                              ])
        md = {}
        rendered = group.render(md)
        self.assertEqual(rendered, 'where\nabc\n')

    def test_render_one_block_set(self):
        group = self._makeOne([('sqlgroup', 'set', lambda x, y:'abc'),
                              ])
        md = {}
        rendered = group.render(md)
        self.assertEqual(rendered, 'set\nabc\n')

    def test_render_multiple_blocks_with_tname(self):
        group = self._makeOne([('sqlgroup', '', lambda x, y:'abc'),
                               ('baz', '', lambda x, y: 'def'),
                               ('qux', '', lambda x, y: 'ghi'),
                              ])
        md = {}
        rendered = group.render(md)
        rendered = ''.join(rendered.split('\n'))
        self.assertEqual(rendered, '(abc baz def qux ghi)')

    def test_render_multiple_blocks_with_tname_noparens(self):
        group = self._makeOne([('sqlgroup', 'noparens', lambda x, y:'abc'),
                               ('baz', '', lambda x, y: 'def'),
                               ('qux', '', lambda x, y: 'ghi'),
                              ])
        md = {}
        rendered = group.render(md)
        rendered = ''.join(rendered.split('\n'))
        self.assertEqual(rendered, 'abc baz def qux ghi')

    def test_render_multiple_blocks_with_tname_and_where(self):
        group = self._makeOne([('sqlgroup', 'where', lambda x, y:'abc'),
                               ('baz', '', lambda x, y: 'def'),
                               ('qux', '', lambda x, y: 'ghi'),
                              ])
        md = {}
        rendered = group.render(md)
        rendered = ''.join(rendered.split('\n'))
        self.assertEqual(rendered, 'where(abc baz def qux ghi)')


    def test_parsed_rendered_complex_where(self):
        # something of a functional test, as we use nvSQL to get parsed.
        from Shared.DC.ZRDB.DA import nvSQL
        template = nvSQL(WHERE_EXAMPLE)
        mapping = {}
        mapping['name'] = 'Goofy'
        mapping['home_town'] = 'Orlando'
        mapping['sql_quote__'] = _sql_quote

        rendered = template(None, mapping)
        self.assertEqual(rendered,
                         'select * from actors\n'
                         'where\n'
                         '((nick_name = "Goofy"\n'
                         ' or first_name = "Goofy"\n)\n'
                         ' and home_town = "Orlando"\n)\n'
                        )

    def test_parsed_rendered_complex_set(self):
        # something of a functional test, as we use nvSQL to get parsed.
        from Shared.DC.ZRDB.DA import nvSQL
        template = nvSQL(UPDATE_EXAMPLE)
        mapping = {}
        mapping['nick_name'] = 'Goofy'
        mapping['home_town'] = 'Orlando'
        mapping['sql_quote__'] = _sql_quote

        rendered = template(None, mapping)
        self.assertEqual(rendered,
                         'update actors\n'
                         'set\nnick_name = "Goofy" , home_town = "Orlando"\n'
                        )

WHERE_EXAMPLE = """\
select * from actors
<dtml-sqlgroup where required>
  <dtml-sqlgroup>
    <dtml-sqltest name column=nick_name type=nb multiple optional>
  <dtml-or>
    <dtml-sqltest name column=first_name type=nb multiple optional>
  </dtml-sqlgroup>
<dtml-and>
  <dtml-sqltest home_town type=nb optional>
<dtml-and>
  <dtml-if minimum_age>
     age >= <dtml-sqlvar minimum_age type=int>
  </dtml-if>
<dtml-and>
  <dtml-if maximum_age>
     age <= <dtml-sqlvar maximum_age type=int>
  </dtml-if>
</dtml-sqlgroup>
"""

UPDATE_EXAMPLE = """\
update actors
<dtml-sqlgroup set noparens>
<dtml-sqltest nick_name type=nb optional>
<dtml-comma>
<dtml-sqltest home_town type=nb optional>
</dtml-sqlgroup>
"""

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SQLGroupTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
