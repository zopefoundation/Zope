
"""Document Template Tests
"""

__rcs_id__='$Id: DTtest.py,v 1.3 1997/11/11 18:39:00 jim Exp $'

############################################################################
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
#  
#
# If you have questions regarding this software,
# contact:
#
#   Jim Fulton, jim@digicool.com
#
#   (540) 371-6909
#
############################################################################ 
__version__='$Revision: 1.3 $'[11:-2]

from DocumentTemplate import *
import sys

class Bruce:
   def __str__(self): return 'bruce'
   def __int__(self): return 42
   def __float__(self): return 42.0
   def keys(self): return ['bruce']*7
   def values(self): return [self]*7
   def items(self): return [('bruce',self)]*7
   def __len__(self): return 7
   def __getitem__(self,index):
       if (type(index) is type(1) and 
	   (index < 0 or index > 6)): raise IndexError, index
       return self
   isDocTemp=0
   def __getattr__(self,name):
       if name[:1]=='_': raise AttributeError, name
       return self
   
bruce=Bruce()    

class arg:
    def __init__(self,nn,aa): self.num, self.arg = nn, aa

class argv:
    def __init__(self):
	import sys
	args=self.args=[]
	for aa in sys.argv[1:]: args.append(arg(len(args)+1,aa))

    def items(self):
	return map(lambda a: ('spam%d' % a.num, a), self.args)

    def values(self): return self.args

def test1():

    aa=argv()

    ss=String(
	"""\
	<html><head><title>Test of documentation templates</title></head>
	<body>
	%(if args)[
	<dl><dt>The arguments to this test program were:<p>
	<dd>
	<ul>
	%(in args)[
	  <li>Argument number %(num)d was %(arg)s
	%(in args)]
	</ul></dl><p>
	%(if args)]
        %(else args)[
	No arguments were given.<p>
        %(else args)]
	And thats da trooth.
	</body></html>
	""")

    print ss(aa)

    print 'num inaccessible:'
    ss.names({'args':'args'})
    print ss(aa)

    print 'quoted source:'
    print str(ss)

    try:
	ss(hello=1,world=2)
	print 'test if test failed'
    except: pass

    # Test nested templates
    a=arg(42,'bruce')
    a.header=HTML("<!--#var arg--> data <!--#var num fmt=%d-->:\n")
    print String("%(header)s number: %(num)d")(a)

def test2():
    # test1()

    aa=argv()

    print HTML(
	'''\
	<html><head><title>Test of documentation templates</title></head>
	<body>
	<!--#if values-->
	  The arguments were:
  	  <!--#in
	  values-->
	      <!--#var
	      sequence-roman-->.
	      Argument <!--#var
	      num fmt=d--> was <!--#var arg-->
	  <!--#/in values-->
	<!--#else values-->
  	  No arguments were given.<p>
	<!--#/if values-->
	And I\'m 100% sure!
	</body></html>
	''')(aa)

def test3():
    test2()

    aa=argv()

    h=HTML(
	'''\
	<html><head><title>Test of documentation templates</title></head>
	<body>
	<!--#if args-->
	  The arguments were:
  	  <!--#in args size=size end=end-->
	      <!--#if previous-sequence-->
                 (<!--#var previous-sequence-start-arg-->-
		  <!--#var previous-sequence-end-arg-->)
	      <!--#/if previous-sequence-->
	      <!--#if sequence-start-->
	         <dl>
	      <!--#/if sequence-start-->
	      <dt><!--#var sequence-arg-->.</dt>
	      <dd>Argument <!--#var num fmt=d--> was <!--#var arg--></dd>
	      <!--#if next-sequence-->
                 (<!--#var next-sequence-start-arg-->-
                  <!--#var next-sequence-end-arg-->)
	      <!--#/if next-sequence-->
	  <!--#/in args-->
	  </dl>
	<!--#else args-->
  	  No arguments were given.<p>
	<!--#/if args-->
	And I\'m 100% sure!
	</body></html>
	''')

    size,orphan=5,0
    for end in range(20):
	end=end+1
	print '='*60, '\n'
	print h(aa,size=size, orphan=orphan, end=end)

def test3_okay(key, val):
    print 'Testing', key
    return 1

def test4():

    def item(key,**kw): return (key,kw)
    def item2(key,**kw): return kw

    class item_class:
	def __init__(self,key,**kw):
	    for k in kw.keys(): self.__dict__[k]=kw[k]

    items=(
	item( 1,dealer='Bay Chevy', make='Chevrolet', model='Caprice', year=96),
	item( 2,dealer='Bay Chevy', make='Chevrolet', model='Nova', year=96),
	item( 4,dealer='Bay Chevy', make='Chevrolet', model='Nova', year=96),
	item( 5,dealer='Bay Chevy', make='Chevrolet', model='Nova', year=96),
	item( 3,dealer='Bay Chevy', make='Chevrolet', model='Corvett', year=96),
	item( 6,dealer='Bay Chevy', make='Chevrolet', model='Lumina', year=96),
	item( 7,dealer='Bay Chevy', make='Chevrolet', model='Lumina', year=96),
	item( 8,dealer='Bay Chevy', make='Chevrolet', model='Lumina', year=95),
	item( 9,dealer='Bay Chevy', make='Chevrolet', model='Corsica', year=96),
	item(10,dealer='Bay Chevy', make='Chevrolet', model='Corsica', year=96),
	item(11,dealer='Bay Chevy', make='Toyota', model='Camry', year=95),
	item(12,dealer='Colman Olds', make='Olds', model='Ciera', year=96),
	item(12,dealer='Colman Olds', make='Olds', model='Ciera', year=96),
	item(12,dealer='Colman Olds', make='Olds', model='Ciera', year=96),
	item(12,dealer='Colman Olds', make='Olds', model='Cutlass', year=96),
	item(12,dealer='Colman Olds', make='Olds', model='Cutlas', year=95),
	item(12,dealer='Colman Olds', make='Dodge', model='Shadow', year=93),
	item(12,dealer='Colman Olds', make='Jeep', model='Cheroke', year=94),
	item(12,dealer='Colman Olds', make='Toyota', model='Previa', year=92),
	item(12,dealer='Colman Olds', make='Toyota', model='Celica', year=93),
	item(12,dealer='Colman Olds', make='Toyota', model='Camry', year=93),
	item(12,dealer='Colman Olds', make='Honda', model='Accord', year=94),
	item(12,dealer='Colman Olds', make='Honda', model='Accord', year=92),
	item(12,dealer='Colman Olds', make='Honda', model='Civic', year=94),
	item(12,dealer='Colman Olds', make='Honda', model='Civix', year=93),
	item( 1,dealer='Spam Chev', make='Chevrolet', model='Caprice', year=96),
	item( 2,dealer='Spam Chev', make='Chevrolet', model='Nova', year=96),
	item( 4,dealer='Spam Chev', make='Chevrolet', model='Nova', year=96),
	item( 5,dealer='Spam Chev', make='Chevrolet', model='Nova', year=96),
	item( 3,dealer='Spam Chev', make='Chevrolet', model='Corvett', year=96),
	item( 6,dealer='Spam Chev', make='Chevrolet', model='Lumina', year=96),
	item( 7,dealer='Spam Chev', make='Chevrolet', model='Lumina', year=96),
	item( 8,dealer='Spam Chev', make='Chevrolet', model='Lumina', year=95),
	item( 9,dealer='Spam Chev', make='Chevrolet', model='Corsica', year=96),
	item(10,dealer='Spam Chev', make='Chevrolet', model='Corsica', year=96),
	item(11,dealer='Spam Chevy', make='Toyota', model='Camry', year=95),
	item(12,dealer='Spam Olds', make='Olds', model='Ciera', year=96),
	item(12,dealer='Spam Olds', make='Olds', model='Ciera', year=96),
	item(12,dealer='Spam Olds', make='Olds', model='Ciera', year=96),
	item(12,dealer='Spam Olds', make='Olds', model='Cutlass', year=96),
	item(12,dealer='Spam Olds', make='Olds', model='Cutlas', year=95),
	item(12,dealer='Spam Olds', make='Dodge', model='Shadow', year=93),
	item(12,dealer='Spam Olds', make='Jeep', model='Cheroke', year=94),
	item(12,dealer='Spam Olds', make='Toyota', model='Previa', year=92),
	item(12,dealer='Spam Olds', make='Toyota', model='Celica', year=93),
	item(12,dealer='Spam Olds', make='Toyota', model='Camry', year=93),
	item(12,dealer='Spam Olds', make='Honda', model='Accord', year=94),
	item(12,dealer='Spam Olds', make='Honda', model='Accord', year=92),
	item(12,dealer='Spam Olds', make='Honda', model='Civic', year=94),
	item(12,dealer='Spam Olds', make='Honda', model='Civix', year=93),
	)

    html=HTML(
	'''\
	<html><head><title>Inventory by Dealer</title></head><body>
	  <dl>
	  <!--#in inventory mapping size=5 start=first_ad-->
	    <!--#if previous-sequence-->
	      <!--#in
	      previous-batches mapping-->
	    	(<!--#var batch-start-var-dealer-->
	    	 <!--#var batch-start-var-year-->
	    	 <!--#var batch-start-var-make-->
	    	 <!--#var batch-start-var-model-->
	    	 -
	    	 <!--#var batch-end-var-dealer-->
	    	 <!--#var batch-end-var-year-->
	    	 <!--#var batch-end-var-make-->
	    	 <!--#var batch-end-var-model-->
	    	 )
	      <!--#/in previous-batches-->
	    <!--#/if previous-sequence-->
	    <!--#if first-dealer-->
	      <dt><!--#var dealer--></dt><dd>
	    <!--#/if first-dealer-->
	    <!--#var year--> <!--#var make--> <!--#var model--> <p>
	    <!--#if last-dealer-->
	      </dd>
	    <!--#/if last-dealer-->
	    <!--#if next-sequence-->
	      <!--#in next-batches mapping-->
	    	(<!--#var batch-start-var-dealer-->
	    	 <!--#var batch-start-var-year-->
	    	 <!--#var batch-start-var-make-->
	    	 <!--#var batch-start-var-model-->
	    	 -
	    	 <!--#var batch-end-var-dealer-->
	    	 <!--#var batch-end-var-year-->
	    	 <!--#var batch-end-var-make-->
	    	 <!--#var batch-end-var-model-->
	    	 )
	      <!--#/in next-batches-->
	    <!--#/if next-sequence-->
	    <!--#/in inventory-->
	  </dl>
	</body></html>
	''')

    print html(inventory=items, first_ad=15)

def test5():
    html=HTML(
	'''\
	<html><head><title>Affiliate Manager Affiliate Menu</title></head><body>

	<CENTER>
	<FONT SIZE="+2">Affiliate Manager Menu</FONT>
	<p>
	
	<!--#if affiliates-->
	Select an affiliate to visit:<br>
	<UL>
	<!--#in affiliates-->
	   <LI><A HREF="<!--#var PARENT_URL-->/<!--#var ID-->/">
	       <!--#var name--></A></LI>
	   <!--#/in affiliates-->
	</UL>
	
	<!--#/if affiliates-->

	<p>
	<A HREF="<!--#var PARENT_URL-->/add_affiliate_form">Add an affiliate</A>
	
	<!--#if affiliates-->
	* <A HREF="<!--#var PARENT_URL-->/delete_affiliates_form">
	Delete affiliates</A>
	<!--#/if affiliates-->

	</p>
	</CENTER>
	</body>
	
	</html>''')

    print html(affiliates=[], PARENT_URL='www')

def test6():
    def d(**kw): return kw
    data=(d(name='jim', age=38),
	  # d(name='kak', age=40),
	  d(name='will', age=7),
	  d(name='drew', age=4),
	  d(name='ches', age=1),
	  )
    html=HTML(
	"""Ages:\n
	<!--#in data mapping-->
	  <!--#if sequence-end-->
	     ---------------
	     for variable name:
	     min:    <!--#var min-name-->
	     max:    <!--#var max-name-->
	     count:  <!--#var count-name-->
	     total:  <!--#var total-name-->
	     median: <!--#var median-name-->
	     ---------------
	     for variable age:
	     min:    <!--#var min-age-->
	     max:    <!--#var max-age-->
	     count:  <!--#var count-age-->
	     total:  <!--#var total-age-->
	     median: <!--#var median-age-->
	     mean:   <!--#var mean-age-->
	     s.d.    <!--#var standard-deviation-age-->
	     ---------------
	  <!--#/if sequence-end-->
	<!--#/in data-->
	""")
    print html(data=data)

def test7():
    import DateTime
    html=HTML("""
    <!--#var name capitalize spacify--> is
    <!--#var date fmt=year-->/<!--#var date fmt=month-->/<!--#var date fmt=day-->
    """)
    html.names({'name':'name', 'date':'date'})
    print html(date=DateTime.DateTime(),
	       name='todays_date')

def test8():
    import DateTime
    html=String("""
    %(name capitalize spacify)s is
    %(date fmt=year)s/%(date fmt=month)s/%(date fmt=day)s
    """)
    print html(date=DateTime.DateTime(),
	       name='todays_date')

def test9():
    html=HTML(
	"""
	<!--#in spam-->
	   <!--#in sequence-item-->
	      <!--#var sequence-item-->
	   <!--#/in sequence-item-->
	<!--#/in spam-->
	""")
    print html(spam=[[1,2,3],[4,5,6]])

def test9a():
    html=HTML(
	"""
	<!--#in spam-->
	   <!--#in sequence-item-->
	      <!--#var sequence-item-->
	   <!--#/in sequence-item-->
	<!--#/in spam-->
	""")
    print html(spam=[[1,2,3],[4,5,6]])

def test10():
    #import Missing
    html=HTML(
	"""
	      <!--#var spam fmt="$%.2f bob's your uncle" null="spam%eggs!|"-->
	""")
    print html(spam=42)
    print html(spam=None)
    #print html(spam=Missing.Value)
    

def test11():
    #import Missing
    html=HTML(
	"""
	          <!--#var spam -->
	html:     <!--#var spam fmt=html-quote-->
	url:      <!--#var spam fmt=url-quote-->
	multi:    <!--#var spam fmt=multi-line-->
	dollars:  <!--#var spam fmt=whole-dollars-->
	cents:    <!--#var spam fmt=dollars-and-cents-->
	dollars,: <!--#var spam fmt=dollars-with-commas-->
	cents,:   <!--#var spam fmt=dollars-and-cents-with-commas-->

	""")
    
    print html(spam=4200000)
    print html(spam=None)
    print html(spam='<a href="spam">\nfoo bar')
    # print html(spam=Missing.Value)
    

class test12ob:
    def __init__(self,**kw):
	for k,v in kw.items(): self.__dict__[k]=v
    def puke(self):
	raise 'Puke', 'raaalf'

def test12():
    class foo:
	def __len__(self): return 9
	def __getitem__(self,i):
	    if i >= 9: raise IndexError, i
	    return test12ob(index=i, value='item %s' % i)

    html=HTML(
	"""
	<!--#if spam-->
	<!--#in spam-->
	   <!--#var value-->
	   <!--#var puke-->
	<!--#/in spam-->
	<!--#/if spam-->
	""")
    try: print html(spam=foo())
    except: return
    raise 'DocumentTemplate bug', (
	'Puke error not properly propigated in test 12')

def main():
	import traceback
	print 'Test 1', '='*60
	try: test1()
	except: traceback.print_exc()
	print 'Test 2', '='*60
	try: test2()
	except: traceback.print_exc()
	print 'Test 3', '='*60
	try: test3()
	except: traceback.print_exc()
	print 'Test 4', '='*60
	try: test4()
	except: traceback.print_exc()
	print 'Test 5', '='*60
	try: test5()
	except: traceback.print_exc()
	print 'Test 6', '='*60
	try: test6()
	except: traceback.print_exc()
	print 'Test 7', '='*60
	try: test7()
	except: traceback.print_exc()
	print 'Test 8', '='*60
	try: test8()
	except: traceback.print_exc()
	print 'Test 9', '='*60
	try: test9()
	except: traceback.print_exc()
	print 'Test 9a', '='*60
	try: test9a()
	except: traceback.print_exc()
	print 'Test 10', '='*60
	try: test10()
	except: traceback.print_exc()
	print 'Test 11', '='*60
	try: test11()
	except: traceback.print_exc()

def test13():
    print HTML('''
    <!--#in items-->
      <!--#var sequence-key-->: <!--#var sequence-item-->
    <!--#/in items-->
    ''')({'spam':'eggs', 'cool':'DC'})
    

if __name__ == "__main__":
    try: command=sys.argv[1]
    except: command='main'
    globals()[command]()

############################################################################
# $Log: DTtest.py,v $
# Revision 1.3  1997/11/11 18:39:00  jim
# Added test for:
# Made sequence-items work when iterating over mapping items.
#
# Revision 1.2  1997/10/27 17:40:02  jim
# Removed old validation machinery.
#
# Revision 1.1  1997/08/27 18:55:44  jim
# initial
#
