
'''Document templates with fill-in fields

Document templates provide for creation of textual documents, such as
HTML pages, from template source by inserting data from python objects
and name-spaces.  Document templates are especially useful when it is
desirable to separate template text from python program source.  For
example, HTML templates may be edited by people who know HTML, and
don\'t know python, while associated python code may be edited by
people who know python but not HTML.

When a document template is created, a collection of default values to
be inserted may be specified with a mapping object and with keyword
arguments.

A document templated may be called to create a document with values
inserted.  When called, an instance, a mapping object, and keyword
arguments may be specified to provide values to be inserted.  If an
instance is provided, the document template will try to look up values
in the instance using getattr, so inheritence of values is supported.
If an inserted value is a function, method, or class, then an attempt
will be made to call the object to obtain values.  This allows
instance methods to be included in documents.

Document templates masquerade as functions, so the python object
publisher (Bobo) will call templates that are stored as instances of
published objects. Bobo will pass the object the template was found in
and the HTTP request object.

Two source formats are supported:

   Extended Python format strings (EPFS) --
      This format is based on the insertion by name format strings
      of python with additional format characters, '[' and ']' to
      indicate block boundaries.  In addition, parameters may be
      used within formats to control how insertion is done.

      For example:

         %%(date fmt=DayOfWeek upper)s

      causes the contents of variable 'date' to be inserted using
      custom format 'DayOfWeek' and with all lower case letters
      converted to upper case.

   HTML --
      This format uses HTML server-side-include syntax with
      commands for inserting text. Parameters may be included to
      customize the operation of a command.

      For example:

         <!--#var total fmt=12.2f-->

      is used to insert the variable 'total' with the C format
      '12.2f'.        

%(Var)s

Document templates support conditional and sequence insertion

    Document templates extend python string substitition rules with a
    mechanism that allows conditional insertion of template text and that
    allows sequences to be inserted with element-wise insertion of
    template text.

    %(If)s

    %(In)s

Accessibility of names:

    The programmer of a module can specify the visibility of all
    attributes available to a Document Template editor in two ways.  A
    mapping object whose keys are accessible attributes and whose
    values are short descriptions can be passed to the document
    template.  Any name not appearing as a key in that list will not
    be acecssible from the document template.  In addition to, or as
    an alternative to, the mapping object, a validation function can
    be specified.  The validation function takes the name and the
    value of the attribute being accessed as arguments and returns a
    non-zero result if the access is allowed.

Document Templates may be created 4 ways:

    DocumentTemplate.String -- Creates a document templated from a
        string using an extended form of python string formatting.

    DocumentTemplate.File -- Creates a document templated bound to a
        named file using an extended form of python string formatting.
        If the object is pickled, the file name, rather than the file
        contents is pickled.  When the object is unpickled, then the
        file will be re-read to obtain the string.  Note that the file
        will not be read until the document template is used the first
        time.

    DocumentTemplate.HTML -- Creates a document templated from a
        string using HTML server-side-include rather than
        python-format-string syntax.

    DocumentTemplate.HTMLFile -- Creates an HTML document template
        from a named file.

%(id)s'''

String__doc__="""Document templates defined from strings.

    Document template strings use an extended form of python string
    formatting.  To insert a named value, simply include text of the
    form: '%(name)x', where 'name' is the name of the value and 'x' is
    a format specification, such as '12.2d'.

    Here are some examples:

	s=DocumentTemplate.String('The total number of hits on %(URL)s '
				  'is %(hits)d.',
				  URL='http://www.digicool.com')
	print s(hits=10)
    
	class url:
	    def hits(self): return self.db['hits']
	    # ...
    
	spam=url()
	# ...
    
	print s(spam)
    
	print s(spam, URL='some other URL')
    
	class cool_web_object:
    
	    fooMethod=DocumentTemplate.File('../private/templates/fooMethod')
	    # Bobo will treat fooMethod just like any other method of cool
	    # web objects, passing self and also passing the HTTP request
	    # as the 'mapping' argument.
    
    
	class arg:
	    def __init__(self,nn,aa): self.num, self.arg = nn, aa
	
	class argv:
	    def __init__(self):
		import sys
		args=self.args=[]
		for aa in sys.argv: args.append(arg(len(args),aa))
	
	def main():
	    # The \"main\" program for this module
	
	    aa=argv()
	
	    ss=HTML(
		'''\
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
		''')
	
	    print ss(aa)
	
	    print 'quoted source:'
	    print str(ss)


    """ 


HTML__doc__="""HTML Document Templates

    HTML Document templates use HTML server-side-include syntax,
    rather than Python format-string syntax.
    
    The HTML document template syntax is illustrated by the following
    example:  

      class arg:
	def __init__(self,nn,aa): self.num, self.arg = nn, aa
    
      class argv:
	def __init__(self):
	    import sys
	    args=self.args=[]
	    for aa in sys.argv: args.append(arg(len(args),aa))

      aa=argv()

      print HTML(
	'''\
	<html><head><title>Test of documentation templates</title></head>
	<body>
	<!--#if args-->
	  The arguments were:
  	  <!--#in args-->
	      <!--#var sequence-letter-->.
	      Argument <!--#var num fmt=d--> was <!--#var arg-->
	  <!--#/in args-->
	<!--#else args-->
  	  No arguments were given.<p>
	<!--#/if args-->
	And I'm 100% sure!
	</body></html>
	''', __names__={'num':'number', 'arg':'argument'})(aa)


	# This is a basic example of batch processing.
	# The previous and following batch is shown.
	html=HTML(
		'''\
		<html><head><title>Inventory by Dealer</title></head><body>
		  <dl>
		  <!--#in inventory mapping size=8 start=first_car overlap-->
		    <!--#if previous-sequence-->
			(<!--#var previous-sequence-start-var-dealer-->
			 <!--#var previous-sequence-start-var-year-->
			 <!--#var previous-sequence-start-var-make-->
			 <!--#var previous-sequence-start-var-model-->
			 -
			 <!--#var previous-sequence-end-var-dealer-->
			 <!--#var previous-sequence-end-var-year-->
			 <!--#var previous-sequence-end-var-make-->
			 <!--#var previous-sequence-end-var-model-->
			 )
		    <!--#/if previous-sequence-->
		    <!--#if first-dealer-->
		      <dt><!--#var dealer--></dt><dd>
		    <!--#/if first-dealer-->
		    <!--#var year--> <!--#var make--> <!--#var model--> <p>
		    <!--#if last-dealer-->
		      </dd>
		    <!--#/if last-dealer-->
		    <!--#if next-sequence-->
			(<!--#var next-sequence-start-var-dealer-->
			 <!--#var next-sequence-start-var-year-->
			 <!--#var next-sequence-start-var-make-->
			 <!--#var next-sequence-start-var-model-->
			 -
			 <!--#var next-sequence-end-var-dealer-->
			 <!--#var next-sequence-end-var-year-->
			 <!--#var next-sequence-end-var-make-->
			 <!--#var next-sequence-end-var-model-->
			 )
		    <!--#/if next-sequence-->
		    <!--#/in inventory-->
		  </dl>
		</body></html>
		''', __names__={'dealer':'Dealer name',
				'make':'Make of car',
				'model':'Car model',
				'year':'Year of manufacture'})
	
	print html(inventory=RDB.File("dealer-inventory.rdb"), first_car=18)
	
	
	# This example provides a fairly sophisticated example of
	# batch processing.  In this case, all prior and following
	# batches are shown.
	html=HTML(
		'''\
		<html><head><title>Inventory by Dealer</title></head><body>
		  <dl>
		  <!--#in inventory mapping size=8 start=first_car overlap-->
		    <!--#if previous-sequence-->
		      <!--#in previous-batches mapping-->
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
		''', __names__={'dealer':'Dealer name',
				'make':'Make of car',
				'model':'Car model',
				'year':'Year of manufacture'})
	
	print html(inventory=RDB.File("dealer-inventory.rdb"), first_car=18)

    HTML document templates quote HTML tags in source when the
    template is converted to a string.  This is handy when templates
    are inserted into HTML editing forms.  """
