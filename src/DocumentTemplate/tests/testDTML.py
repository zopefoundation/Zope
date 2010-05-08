##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Document Template Tests
"""

import unittest

class DTMLTests(unittest.TestCase):

    def _get_doc_class(self):
        from DocumentTemplate.DT_HTML import HTML
        return HTML
    doc_class = property(_get_doc_class,)

    def testBatchingEtc(self):

        def item(key, **kw):
            return (key, kw)

        items=(
            item( 1,dealer='Bay Chevy', make='Chevrolet',
                  model='Caprice', year=96),
            item( 2,dealer='Bay Chevy', make='Chevrolet',
                  model='Nova', year=96),
            item( 4,dealer='Bay Chevy', make='Chevrolet',
                  model='Nova', year=96),
            item( 5,dealer='Bay Chevy', make='Chevrolet',
                  model='Nova', year=96),
            item( 3,dealer='Bay Chevy', make='Chevrolet',
                  model='Corvett', year=96),
            item( 6,dealer='Bay Chevy', make='Chevrolet',
                  model='Lumina', year=96),
            item( 7,dealer='Bay Chevy', make='Chevrolet',
                  model='Lumina', year=96),
            item( 8,dealer='Bay Chevy', make='Chevrolet',
                  model='Lumina', year=95),
            item( 9,dealer='Bay Chevy', make='Chevrolet',
                  model='Corsica', year=96),
            item(10,dealer='Bay Chevy', make='Chevrolet',
                 model='Corsica', year=96),
            item(11,dealer='Bay Chevy', make='Toyota',
                 model='Camry', year=95),
            item(12,dealer='Colman Olds', make='Olds',
                 model='Ciera', year=96),
            item(12,dealer='Colman Olds', make='Olds',
                 model='Ciera', year=96),
            item(12,dealer='Colman Olds', make='Olds',
                 model='Ciera', year=96),
            item(12,dealer='Colman Olds', make='Olds',
                 model='Cutlass', year=96),
            item(12,dealer='Colman Olds', make='Olds',
                 model='Cutlas', year=95),
            item(12,dealer='Colman Olds', make='Dodge',
                 model='Shadow', year=93),
            item(12,dealer='Colman Olds', make='Jeep',
                 model='Cheroke', year=94),
            item(12,dealer='Colman Olds', make='Toyota',
                 model='Previa', year=92),
            item(12,dealer='Colman Olds', make='Toyota',
                 model='Celica', year=93),
            item(12,dealer='Colman Olds', make='Toyota',
                 model='Camry', year=93),
            item(12,dealer='Colman Olds', make='Honda',
                 model='Accord', year=94),
            item(12,dealer='Colman Olds', make='Honda',
                 model='Accord', year=92),
            item(12,dealer='Colman Olds', make='Honda',
                 model='Civic', year=94),
            item(12,dealer='Colman Olds', make='Honda',
                 model='Civix', year=93),
            item( 1,dealer='Spam Chev', make='Chevrolet',
                  model='Caprice', year=96),
            item( 2,dealer='Spam Chev', make='Chevrolet',
                  model='Nova', year=96),
            item( 4,dealer='Spam Chev', make='Chevrolet',
                  model='Nova', year=96),
            item( 5,dealer='Spam Chev', make='Chevrolet',
                  model='Nova', year=96),
            item( 3,dealer='Spam Chev', make='Chevrolet',
                  model='Corvett', year=96),
            item( 6,dealer='Spam Chev', make='Chevrolet',
                  model='Lumina', year=96),
            item( 7,dealer='Spam Chev', make='Chevrolet',
                  model='Lumina', year=96),
            item( 8,dealer='Spam Chev', make='Chevrolet',
                  model='Lumina', year=95),
            item( 9,dealer='Spam Chev', make='Chevrolet',
                  model='Corsica', year=96),
            item(10,dealer='Spam Chev', make='Chevrolet',
                 model='Corsica', year=96),
            item(11,dealer='Spam Chevy', make='Toyota',
                 model='Camry', year=95),
            item(12,dealer='Spam Olds', make='Olds',
                 model='Ciera', year=96),
            item(12,dealer='Spam Olds', make='Olds',
                 model='Ciera', year=96),
            item(12,dealer='Spam Olds', make='Olds',
                 model='Ciera', year=96),
            item(12,dealer='Spam Olds', make='Olds',
                 model='Cutlass', year=96),
            item(12,dealer='Spam Olds', make='Olds',
                 model='Cutlas', year=95),
            item(12,dealer='Spam Olds', make='Dodge',
                 model='Shadow', year=93),
            item(12,dealer='Spam Olds', make='Jeep',
                 model='Cheroke', year=94),
            item(12,dealer='Spam Olds', make='Toyota',
                 model='Previa', year=92),
            item(12,dealer='Spam Olds', make='Toyota',
                 model='Celica', year=93),
            item(12,dealer='Spam Olds', make='Toyota',
                 model='Camry', year=93),
            item(12,dealer='Spam Olds', make='Honda',
                 model='Accord', year=94),
            item(12,dealer='Spam Olds', make='Honda',
                 model='Accord', year=92),
            item(12,dealer='Spam Olds', make='Honda',
                 model='Civic', year=94),
            item(12,dealer='Spam Olds', make='Honda',
                 model='Civix', year=93),
            )

        html=self.doc_class(read_file('dealers.dtml'))
        res = html(inventory=items, first_ad=15)
        expected = read_file('dealers.out')
        self.assertEqual(res,expected)

    def testSequenceSummaries(self):
        data=(dict(name='jim', age=38),
              # dict(name='kak', age=40),
              dict(name='will', age=7),
              dict(name='drew', age=4),
              dict(name='ches', age=1),
              )
        html = self.doc_class('<dtml-in data mapping>'
                    '<dtml-if sequence-end>'
                    'Variable "name": '
                    'min=<dtml-var min-name> '
                    'max=<dtml-var max-name> '
                    'count=<dtml-var count-name> '
                    'total=<dtml-var total-name> '
                    'median=<dtml-var median-name> '
                    'Variable "age": '
                    'min=<dtml-var min-age> '
                    'max=<dtml-var max-age> '
                    'count=<dtml-var count-age> '
                    'total=<dtml-var total-age> '
                    'median=<dtml-var median-age> '
                    'mean=<dtml-var mean-age> '
                    '<dtml-let sda=standard-deviation-age>'
                    's.d.=<dtml-var expr="_.int(sda)">'
                    '</dtml-let>'
                    '</dtml-if sequence-end>'
                    '</dtml-in data>')
        res = html(data=data)
        expected = ('Variable "name": min=ches max=will count=4 total= '
                    'median=between jim and drew '
                    'Variable "age": min=1 max=38 count=4 total=50 '
                    'median=5 mean=12.5 s.d.=17')
        assert res == expected, res

    def testDTMLDateFormatting(self):
        import DateTime
        html = self.doc_class(
        "<dtml-var name capitalize spacify> is "
        "<dtml-var date fmt=year>/<dtml-var date "
                    "fmt=month>/<dtml-var date fmt=day>")
        res = html(date=DateTime.DateTime("1995-12-25"),
                   name='christmas_day')
        expected = 'Christmas day is 1995/12/25'
        assert res == expected, res

    def testSimpleString(self):
        from DocumentTemplate.DT_HTML import String
        dt = String('%(name)s')
        res = dt(name='Chris')
        expected = 'Chris'
        assert res == expected, res

    def testStringDateFormatting(self):
        import DateTime
        from DocumentTemplate.DT_HTML import String
        html = String("%(name capitalize spacify)s is "
                      "%(date fmt=year)s/%(date fmt=month)s/%(date fmt=day)s")
        res = html(date=DateTime.DateTime("2001-04-27"),
                   name='the_date')
        expected = 'The date is 2001/4/27'
        assert res == expected, res

    def testSequence1(self):
        html=self.doc_class(
            '<dtml-in spam><dtml-in sequence-item><dtml-var sequence-item> '
            '</dtml-in sequence-item></dtml-in spam>')
        expected = '1 2 3 4 5 6 '
        res = html(spam=[[1,2,3],[4,5,6]])
        assert res == expected, res

    def testSequence2(self):
        html=self.doc_class(
            '<dtml-in spam><dtml-in sequence-item><dtml-var sequence-item>-'
            '</dtml-in sequence-item></dtml-in spam>')
        expected = '1-2-3-4-5-6-'
        res = html(spam=[[1,2,3],[4,5,6]])
        assert res == expected, res

    def testNull(self):
        html=self.doc_class('<dtml-var spam fmt="$%.2f bobs your uncle" '
                  'null="spam%eggs!|">')
        expected = '$42.00 bobs your unclespam%eggs!|'
        res = html(spam=42) + html(spam=None)
        assert res == expected, res

    def testUrlUnquote(self):
        html1 = self.doc_class(
            """
            <dtml-var expr="'http%3A//www.zope.org%3Fa%3Db%20123'" fmt=url-unquote>
            """
            )
        html2 = self.doc_class(
            """
            <dtml-var expr="'http%3A%2F%2Fwww.zope.org%3Fa%3Db+123'" fmt=url-unquote-plus>
            """
            )

        expected = (
            """
            http://www.zope.org?a=b 123
            """
            )
        self.assertEqual(html1(), expected)
        self.assertEqual(html2(), expected)
        html1 = self.doc_class(
            """
            <dtml-var expr="'http%3A//www.zope.org%3Fa%3Db%20123'" url_unquote>
            """
            )
        html2 = self.doc_class(
            """
            <dtml-var expr="'http%3A%2F%2Fwww.zope.org%3Fa%3Db+123'" url_unquote_plus>
            """
            )

        expected = (
            """
            http://www.zope.org?a=b 123
            """
            )
        self.assertEqual(html1(), expected)
        self.assertEqual(html2(), expected)


    def test_fmt(self):
        html=self.doc_class(
            """
            <dtml-var spam>
            html=<dtml-var spam fmt=html-quote>
            url=<dtml-var spam fmt=url-quote>
            multi=<dtml-var spam fmt=multi-line>
            dollars=<dtml-var spam fmt=whole-dollars>
            cents=<dtml-var spam fmt=dollars-and-cents>
            dollars,=<dtml-var spam fmt=dollars-with-commas>
            cents,=<dtml-var spam fmt=dollars-and-cents-with-commas>""")

        expected = (
            '''
            4200000
            html=4200000
            url=4200000
            multi=4200000
            dollars=$4200000
            cents=$4200000.00
            dollars,=$4,200,000
            cents,=$4,200,000.00
            None
            html=None
            url=None
            multi=None
            dollars=
            cents=
            dollars,=
            cents,=
            <a href="spam">
foo bar
            html=&lt;a href=&quot;spam&quot;&gt;
foo bar
            url=%3Ca%20href%3D%22spam%22%3E%0Afoo%20bar
            multi=<a href="spam"><br />
foo bar
            dollars=
            cents=
            dollars,=
            cents,=''')

        res = html(spam=4200000) + html(spam=None) + html(
            spam='<a href="spam">\nfoo bar')
        self.assertEqual(res,expected)

    def test_fmt_reST_include_directive_raises(self):
        source = '.. include:: /etc/passwd'
        html = self.doc_class('<dtml-var name="foo" fmt="restructured-text">')
        html._vars['foo'] = source
        result = html()

        # The include: directive hasn't been rendered, it remains
        # verbatimly in the rendered output.  Instead a warning
        # message is presented:
        self.assert_(source in result)
        self.assert_(docutils_include_warning in result)

    def test_fmt_reST_raw_directive_disabled(self):
        from cgi import escape
        EXPECTED = '<h1>HELLO WORLD</h1>'
        source = '.. raw:: html\n\n  %s\n' % EXPECTED
        html = self.doc_class('<dtml-var name="foo" fmt="restructured-text">')
        html._vars['foo'] = source
        result = html()

        # The raw: directive hasn't been rendered, it remains
        # verbatimly in the rendered output.  Instead a warning
        # message is presented:
        self.assert_(EXPECTED not in result)
        self.assert_(escape(EXPECTED) in result)
        self.assert_(docutils_raw_warning in result)

    def test_fmt_reST_raw_directive_file_option_raises(self):
        source = '.. raw:: html\n  :file: inclusion.txt'
        html = self.doc_class('<dtml-var name="foo" fmt="restructured-text">')
        html._vars['foo'] = source
        result = html()

        # The raw: directive hasn't been rendered, it remains
        # verbatimly in the rendered output.  Instead a warning
        # message is presented:
        self.assert_(source in result)
        self.assert_(docutils_raw_warning in result)

    def test_fmt_reST_raw_directive_url_option_raises(self):
        source = '.. raw:: html\n  :url: http://www.zope.org'
        html = self.doc_class('<dtml-var name="foo" fmt="restructured-text">')
        html._vars['foo'] = source
        result = html()

        # The raw: directive hasn't been rendered, it remains
        # verbatimly in the rendered output.  Instead a warning
        # message is presented:
        self.assert_(source in result)
        self.assert_(docutils_raw_warning in result)

    def testPropogatedError(self):
        from ExtensionClass import Base

        class foo:
            def __len__(self): return 9
            def __getitem__(self,i):
                if i >= 9: raise IndexError, i
                return self.testob(i)

            class testob (Base):
                __roles__ = None  # Public
                def __init__(self, index):
                    self.index = index
                    self.value = 'item %s' % index

                getValue__roles__ = None  # Public
                def getValue(self):
                    return self.value

                puke__roles__ = None  # Public
                def puke(self):
                    raise PukeError('raaalf')

        html=self.doc_class(
            """
            <dtml-if spam>
            <dtml-in spam>
            <dtml-var getValue>
            <dtml-var puke>
            </dtml-in spam>
            </dtml-if spam>
            """)
        try:
            html(spam=foo())
        except PukeError:
            # Passed the test.
            pass
        else:
            assert 0, 'Puke error not propogated'

    def testRenderCallable(self):
        #Test automatic rendering of callable objects
        from ExtensionClass import Base
        class C (Base):
            __allow_access_to_unprotected_subobjects__ = 1
            x=1
            def y(self): return self.x*2
        C.h = self.doc_class("The h method, <dtml-var x> <dtml-var y>")
        C.h2 = self.doc_class("The h2 method")

        expected = "1, 2, The h method, 1 2"
        res = self.doc_class("<dtml-var x>, <dtml-var y>, <dtml-var h>")(C())
        assert res == expected, res

        expected = (
            '''
            1,
            2,
            The h2 method''')
        res = self.doc_class(
            '''
            <dtml-var expr="_.render(i.x)">,
            <dtml-var expr="_.render(i.y)">,
            <dtml-var expr="_.render(i.h2)">''')(i=C())
        assert res == expected, res

    def testWith(self):
        class person:
            __allow_access_to_unprotected_subobjects__ = 1
            name='Jim'
            height_inches=73

        expected = 'Hi, my name is %s and my height is %d cm.' % (
            person.name, int(person.height_inches * 2.54))

        res = self.doc_class(
            '<dtml-with person>Hi, my name is <dtml-var name> '
            'and my height is <dtml-var "_.int(height_inches*2.54)"> '
            'cm.</dtml-with>')(person=person)
        assert res == expected, res

    def testRaise(self):
        try:
            res = self.doc_class(
            "<dtml-raise IndexError>success!</dtml-raise>")()
        except IndexError, v:
            res = v
        assert str(res) == 'success!', `res`


    def testNoItemPush(self):
        data = dict(sec='B',
                    name='XXX',
                    sub=(dict(name='b1'), dict(name='b2',sec='XXX')))
        html = """
<dtml-with data mapping><dtml-in sub no_push_item>
    <dtml-var sec>.<dtml-with sequence-item mapping><dtml-var name></dtml-with>
</dtml-in></dtml-with>
"""
        expected = """
    B.b1    B.b2"""
        result = self.doc_class(html)(data=data)
        assert result == expected, result

    def testBasicHTMLIn(self):
        data=(
            dict(name='jim', age=39),
            dict(name='kak', age=29),
            dict(name='will', age=8),
            dict(name='andrew', age=5),
            dict(name='chessie',age=2),
            )

        html="""
<!--#in data mapping-->
   <!--#var name-->, <!--#var age-->
<!--#/in-->
"""
        expected = """
   jim, 39
   kak, 29
   will, 8
   andrew, 5
   chessie, 2
"""
        result = self.doc_class(html)(data=data)
        assert result == expected, result

    def testBasicHTMLIn2(self):
        xxx=(Dummy(name=1), Dummy(name=2), Dummy(name=3))
        html = """
<!--#in xxx-->
   <!--#var name  -->
<!--#/in-->
"""
        expected = """
   1
   2
   3
"""
        result = self.doc_class(html)(xxx=xxx)
        assert result == expected, result

    def testBasicHTMLIn3(self):
        ns = {'prop_ids': ('title', 'id'), 'title': 'good', 'id': 'times'}
        html = """:<dtml-in prop_ids><dtml-var sequence-item>=<dtml-var
        expr="_[_['sequence-item']]">:</dtml-in>"""
        result = self.doc_class(html)(None, ns)
        expected = ":title=good:id=times:"

        assert result == expected, result

    def testHTMLInElse(self):
        xxx=(Dummy(name=1), Dummy(name=2), Dummy(name=3))
        html="""
<!--#in data mapping-->
<!--#var name-->, <!--#var age-->
<!--#else-->
<!--#in xxx-->
<!--#var name -->
<!--#/in-->
<!--#/in-->
"""
        expected = """
1
2
3
"""
        result = self.doc_class(html)(xxx=xxx, data={})
        assert result == expected, result

    def testBasicStringIn(self):
        from DocumentTemplate.DT_HTML import String
        data=(
            dict(name='jim', age=39),
            dict(name='kak', age=29),
            dict(name='will', age=8),
            dict(name='andrew', age=5),
            dict(name='chessie',age=2),
            )
        s="""
%(in data mapping)[
   %(name)s, %(age)s
%(in)]
"""
        expected = """
   jim, 39
   kak, 29
   will, 8
   andrew, 5
   chessie, 2
"""
        result = String(s)(data=data)
        assert expected == result, result


def read_file(name):
    import os
    from DocumentTemplate import tests
    here = tests.__path__[0]
    f = open(os.path.join(here, name), 'r')
    res = f.read()
    f.close()
    return res

class Dummy:
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Dummy(%s)" % `self.__dict__`

docutils_include_warning = '''\
<p class="system-message-title">System Message: WARNING/2 (<tt class="docutils">&lt;string&gt;</tt>, line 1)</p>
<p>&quot;include&quot; directive disabled.</p>'''

docutils_raw_warning = '''\
<p class="system-message-title">System Message: WARNING/2 (<tt class="docutils">&lt;string&gt;</tt>, line 1)</p>
<p>&quot;raw&quot; directive disabled.</p>'''

class PukeError(Exception):
    """Exception raised in test code."""

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( DTMLTests ) )
    return suite
