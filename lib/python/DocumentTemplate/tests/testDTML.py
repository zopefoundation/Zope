##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""Document Template Tests
"""

__rcs_id__='$Id: testDTML.py,v 1.4 2001/04/28 22:36:45 chrism Exp $'
__version__='$Revision: 1.4 $'[11:-2]

import sys, os
import unittest

if __name__=='__main__':
    sys.path.append(os.path.join(os.pardir, os.pardir))
    here = os.curdir
else:
    from App.Common import package_home
    here = package_home(globals())

def read_file(name):
    f = open(os.path.join(here, name), 'rb')
    res = f.read()
    f.close()
    return res

from DocumentTemplate import HTML, String
from ExtensionClass import Base
class D:
    def __init__(self, **kw):
        for k, v in kw.items(): self.__dict__[k]=v

    def __repr__(self): return "D(%s)" % `self.__dict__`

def d(**kw): return kw


class DTMLTests (unittest.TestCase):

    doc_class = HTML

    def checkBatchingEtc(self):

        def item(key,**kw): return (key,kw)
        def item2(key,**kw): return kw

        class item_class:
            def __init__(self,key,**kw):
                for k in kw.keys(): self.__dict__[k]=kw[k]

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
        assert res == expected, res

    def checkSequenceSummaries(self):
        def d(**kw): return kw
        data=(d(name='jim', age=38),
              # d(name='kak', age=40),
              d(name='will', age=7),
              d(name='drew', age=4),
              d(name='ches', age=1),
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

    def checkDTMLDateFormatting(self):
        import DateTime
        html = self.doc_class(
        "<dtml-var name capitalize spacify> is "
        "<dtml-var date fmt=year>/<dtml-var date "
                    "fmt=month>/<dtml-var date fmt=day>")
        res = html(date=DateTime.DateTime("1995-12-25"),
                   name='christmas_day')
        expected = 'Christmas day is 1995/12/25'
        assert res == expected, res

    def checkSimpleString(self):
        dt = String('%(name)s')
        res = dt(name='Chris')
        expected = 'Chris'
        assert res == expected, res

    def checkStringDateFormatting(self):
        import DateTime
        html = String("%(name capitalize spacify)s is "
                      "%(date fmt=year)s/%(date fmt=month)s/%(date fmt=day)s")
        res = html(date=DateTime.DateTime("2001-04-27"),
                   name='the_date')
        expected = 'The date is 2001/4/27'
        assert res == expected, res

    def checkSequence1(self):
        html=self.doc_class(
            '<dtml-in spam><dtml-in sequence-item><dtml-var sequence-item> '
            '</dtml-in sequence-item></dtml-in spam>')
        expected = '1 2 3 4 5 6 '
        res = html(spam=[[1,2,3],[4,5,6]])
        assert res == expected, res

    def checkSequence2(self):
        html=self.doc_class(
            '<dtml-in spam><dtml-in sequence-item><dtml-var sequence-item>-'
            '</dtml-in sequence-item></dtml-in spam>')
        expected = '1-2-3-4-5-6-'
        res = html(spam=[[1,2,3],[4,5,6]])
        assert res == expected, res

    def checkNull(self):
        html=self.doc_class('<dtml-var spam fmt="$%.2f bobs your uncle" '
                  'null="spam%eggs!|">')
        expected = '$42.00 bobs your unclespam%eggs!|'
        res = html(spam=42) + html(spam=None)
        assert res == expected, res

    def check_fmt(self):
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
            multi=<a href="spam"><br>
foo bar
            dollars=
            cents=
            dollars,=
            cents,=''')

        res = html(spam=4200000) + html(spam=None) + html(
            spam='<a href="spam">\nfoo bar')
        assert res == expected, res

    def checkPropogatedError(self):

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
                    raise 'Puke', 'raaalf'

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
        except 'Puke':
            # Passed the test.
            pass
        else:
            assert 0, 'Puke error not propogated'

    def checkRenderCallable(self):
        "Test automatic rendering of callable objects"
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

    def checkWith(self):
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

    def checkRaise(self):
        try:
            res = self.doc_class(
            "<dtml-raise IndexError>success!</dtml-raise>")()
        except IndexError, v:
            res = v
        assert str(res) == 'success!', `res`


    def checkBasicHTMLIn(self):
        data=(
            d(name='jim', age=39),
            d(name='kak', age=29),
            d(name='will', age=8),
            d(name='andrew', age=5),
            d(name='chessie',age=2),
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
        result = HTML(html)(data=data)
        assert result == expected, result

    def checkBasicHTMLIn2(self):
        xxx=(D(name=1), D(name=2), D(name=3))
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
        result = HTML(html)(xxx=xxx)
        assert result == expected, result

    def checkHTMLInElse(self):
        xxx=(D(name=1), D(name=2), D(name=3))
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
        result = HTML(html)(xxx=xxx, data={})
        assert result == expected, result
        
    def checkBasicStringIn(self):
        data=(
            d(name='jim', age=39),
            d(name='kak', age=29),
            d(name='will', age=8),
            d(name='andrew', age=5),
            d(name='chessie',age=2),
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
        
def test_suite():
    return unittest.makeSuite(DTMLTests, 'check')

def main():
    alltests = test_suite()
    runner = unittest.TextTestRunner()
    runner.run(alltests)

def debug():
   test_suite().debug()

def pdebug():
    import pdb
    pdb.run('debug()')

if __name__=='__main__':
    if len(sys.argv) > 1:
        globals()[sys.argv[1]]()
    else:
        main()
