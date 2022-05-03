##########################
Appendix A: DTML Reference
##########################

.. include:: includes/zope2_notice.rst

DTML is the *Document Template Markup Language*, a handy presentation and
templating language that comes with Zope. This Appendix is a reference to all
of DTMLs markup tags and how they work.

call: Call a method
===================

The 'call' tag lets you call a method without inserting the results into the
DTML output.

Syntax
------

'call' tag syntax::

  <dtml-call Variable|expr="Expression">

If the call tag uses a variable, the methods arguments are passed automatically
by DTML just as with the 'var' tag. If the method is specified in a expression,
then you must pass the arguments yourself.

Examples
--------

Calling by variable name::

  <dtml-call UpdateInfo>

This calls the 'UpdateInfo' object automatically passing arguments.

Calling by expression::

  <dtml-call expr="RESPONSE.setHeader('content-type', 'text/plain')">

See Also
--------

- var tag


comment: Comments DTML
======================

The comment tag lets you document your DTML with comments. You can also use it
to temporarily disable DTML tags by commenting them out.

Syntax
------

'comment' tag syntax::

  <dtml-comment>
  </dtml-comment>

The 'comment' tag is a block tag. The contents of the block are not executed,
nor are they inserted into the DTML output.

Examples
--------

Documenting DTML::

  <dtml-comment>
    This content is not executed and does not appear in the output.
  </dtml-comment>

Commenting out DTML::

  <dtml-comment>
    This DTML is disabled and will not be executed.
    <dtml-call someMethod>
  </dtml-comment>

Zope still validates the DTML inside the comment block and will not save any
comments that are not valid DTML. It is also not possible to comment in a way
that breaks code flow, for example you cannot inproperly nest a comment and a
dtml-in.


functions: DTML Functions
=========================

DTML utility functions provide some Python built-in functions and some
DTML-specific functions.

Functions
---------

abs(number)
  Return the absolute value of a number. The argument may be a plain or long
  integer or a floating point number. If the argument is a complex number, its
  magnitude is returned.

chr(integer)
  Return a string of one character whose ASCII code is the integer, e.g.,
  'chr(97)' returns the string 'a'. This is the inverse of ord(). The argument
  must be in the range 0 to 255, inclusive; 'ValueError' will be raised if the
  integer is outside that range.

DateTime()
  Returns a Zope 'DateTime' object given constructor arguments. See the
  DateTime API reference for more information on constructor arguments.

divmod(number, number)
  Take two numbers as arguments and return a pair of numbers consisting of
  their quotient and remainder when using long division. With mixed operand
  types, the rules for binary arithmetic operators apply. For plain and long
  integers, the result is the same as '(a / b, a % b)'. For floating point
  numbers the result is '(q, a % b)', where *q* is usually 'math.floor(a / b)'
  but may be 1 less than that. In any case 'q * b + a % b' is very close to
  *a*, if 'a % b' is non-zero it has the same sign as *b*, and '0 <= abs(a % b)
  < abs(b)'.

float(number)
  Convert a string or a number to floating point. If the argument is a string,
  it must contain a possibly signed decimal or floating point number, possibly
  embedded in whitespace; this behaves identical to 'string.atof(number)'.
  Otherwise, the argument may be a plain or long integer or a floating point
  number, and a floating point number with the same value (within Python's
  floating point precision) is returned.

getattr(object, string)
  Return the value of the named attributed of object. name must be a string. If
  the string is the name of one of the object's attributes, the result is the
  value of that attribute. For example, 'getattr(x, "foobar")' is equivalent to
  'x.foobar'. If the named attribute does not exist, default is returned if
  provided, otherwise 'AttributeError' is raised.

getitem(variable, render=0)
  Returns the value of a DTML variable. If 'render' is true, the variable is
  rendered. See the 'render' function.

hasattr(object, string)
  The arguments are an object and a string. The result is 1 if the string is
  the name of one of the object's attributes, 0 if not. (This is implemented by
  calling getattr(object, name) and seeing whether it raises an exception or
  not.)

hash(object)
  Return the hash value of the object (if it has one). Hash values are
  integers. They are used to quickly compare dictionary keys during a
  dictionary lookup. Numeric values that compare equal have the same hash value
  (even if they are of different types, e.g. 1 and 1.0).

has_key(variable)
  Returns true if the DTML namespace contains the named variable.

hex(integer)
  Convert an integer number (of any size) to a hexadecimal string. The result
  is a valid Python expression. Note: this always yields an unsigned literal,
  e.g. on a 32-bit machine, 'hex(-1)' yields '0xffffffff'. When evaluated on a
  machine with the same word size, this literal is evaluated as -1; at a
  different word size, it may turn up as a large positive number or raise an
  'OverflowError' exception.

int(number)
  Convert a string or number to a plain integer. If the argument is a string,
  it must contain a possibly signed decimal number representable as a Python
  integer, possibly embedded in whitespace; this behaves identical to
  'string.atoi(number[, radix]'). The 'radix' parameter gives the base for the
  conversion and may be any integer in the range 2 to 36. If 'radix' is
  specified and the number is not a string, 'TypeError' is raised. Otherwise,
  the argument may be a plain or long integer or a floating point number.
  Conversion of floating point numbers to integers is defined by the C
  semantics; normally the conversion truncates towards zero.

len(sequence)
  Return the length (the number of items) of an object. The argument may be a
  sequence (string, tuple or list) or a mapping (dictionary).

max(s)
  With a single argument s, return the largest item of a non-empty sequence
  (e.g., a string, tuple or list). With more than one argument, return the
  largest of the arguments.

min(s)
  With a single argument s, return the smallest item of a non-empty sequence
  (e.g., a string, tuple or list). With more than one argument, return the
  smallest of the arguments.

namespace([name=value]...)
  Returns a new DTML namespace object. Keyword argument 'name=value' pairs are
  pushed into the new namespace.

oct(integer)
  Convert an integer number (of any size) to an octal string. The result is a
  valid Python expression. Note: this always yields an unsigned literal, e.g.
  on a 32-bit machine, 'oct(-1)' yields '037777777777'. When evaluated on a
  machine with the same word size, this literal is evaluated as -1; at a
  different word size, it may turn up as a large positive number or raise an
  OverflowError exception.

ord(character)
  Return the ASCII value of a string of one character. E.g., 'ord("a")' returns
  the integer 97. This is the inverse of 'chr()'.

pow(x, y [,z])
  Return *x* to the power *y*; if *z* is present, return *x* to the power *y*,
  modulo *z* (computed more efficiently than 'pow(x, y) % z'). The arguments
  must have numeric types. With mixed operand types, the rules for binary
  arithmetic operators apply. The effective operand type is also the type of
  the result; if the result is not expressible in this type, the function
  raises an exception; e.g., 'pow(2, -1)' or 'pow(2, 35000)' is not allowed.

range([start,] stop [,step])
  This is a versatile function to create lists containing arithmetic
  progressions. The arguments must be plain integers. If the step argument is
  omitted, it defaults to 1. If the start argument is omitted, it defaults to
  0. The full form returns a list of plain integers '[start, start + step,
  start + 2 * step, ...]'. If step is positive, the last element is the largest
  'start + i * step' less than *stop*; if *step* is negative, the last element
  is the largest 'start + i * step' greater than *stop*. *step* must not be
  zero (or else 'ValueError' is raised).

round(x [,n])
  Return the floating point value *x* rounded to *n* digits after the decimal
  point. If n is omitted, it defaults to zero. The result is a floating point
  number. Values are rounded to the closest multiple of 10 to the power minus
  n; if two multiples are equally close, rounding is done away from 0 (so e.g.
  round(0.5) is 1.0 and round(-0.5) is -1.0).

render(object)
  Render 'object'. For DTML objects this evaluates the DTML code with the
  current namespace. For other objects, this is equivalent to 'str(object)'.

reorder(s [,with] [,without])
  Reorder the items in s according to the order given in 'with' and without the
  items mentioned in 'without'. Items from s not mentioned in with are removed.
  s, with, and without are all either sequences of strings or sequences of
  key-value tuples, with ordering done on the keys. This function is useful for
  constructing ordered select lists.

SecurityCalledByExecutable()
  Return a true if the current object (e.g. DTML document or method) is being
  called by an executable (e.g. another DTML document or method, a script or a
  SQL method).

SecurityCheckPermission(permission, object)
  Check whether the security context allows the given permission on the given
  object. For example, 'SecurityCheckPermission("Add Documents, Images, and
  Files", this())' would return true if the current user was authorized to
  create documents, images, and files in the current location.

SecurityGetUser()
  Return the current user object. This is normally the same as the
  'REQUEST.AUTHENTICATED_USER' object. However, the 'AUTHENTICATED_USER' object
  is insecure since it can be replaced.

SecurityValidate([object] [,parent] [,name] [,value])
  Return true if the value is accessible to the current user. 'object' is the
  object the value was accessed in, 'parent' is the container of the value, and
  'name' is the named used to access the value (for example, if it was obtained
  via 'getattr'). You may omit some of the arguments, however it is best to
  provide all available arguments.

SecurityValidateValue(object)
  Return true if the object is accessible to the current user. This function is
  the same as calling 'SecurityValidate(None, None, None, object)'.

str(object)
  Return a string containing a nicely printable representation of an object.
  For strings, this returns the string itself.

test(condition, result [,condition, result]... [,default])
  Takes one or more condition, result pairs and returns the result of the first
  true condition. Only one result is returned, even if more than one condition
  is true. If no condition is true and a default is given, the default is
  returned. If no condition is true and there is no default, None is returned.

unichr(number)
  Return a unicode string representing the value of number as a unicode
  character. This is the inverse of ord() for unicode characters.

unicode(string[, encoding[, errors ] ])
  Decodes string using the codec for encoding. Error handling is done according
  to errors. The default behavior is to decode UTF-8 in strict mode, meaning
  that encoding errors raise ValueError.

Attributes
----------

None
  The 'None' object is equivalent to the Python built-in object 'None'. This is
  usually used to represent a Null or false value.

See Also
--------

- `string module <https://docs.python.org/library/string.html>`_

- `random module <https://docs.python.org/library/random.html>`_

- `math module <https://docs.python.org/library/math.html>`_

- `sequence module <https://docs.python.org/library/functions.html>`_


if: Tests Conditions
====================

The 'if' tags allows you to test conditions and to take different actions
depending on the conditions. The 'if' tag mirrors Python's 'if/elif/else'
condition testing statements.

Syntax
------

If tag syntax::

  <dtml-if ConditionVariable|expr="ConditionExpression">
  [<dtml-elif ConditionVariable|expr="ConditionExpression">]
   ...
  [<dtml-else>]
  </dtml-if>

The 'if' tag is a block tag. The 'if' tag and optional 'elif' tags
take a condition variable name or a condition expression, but not
both. If the condition name or expression evaluates to true then
the 'if' block is executed. True means not zero, an empty string
or an empty list.  If the condition variable is not found then the
condition is considered false.

If the initial condition is false, each 'elif' condition is tested
in turn. If any 'elif' condition is true, its block is
executed. Finally the optional 'else' block is executed if none of
the 'if' and 'elif' conditions were true. Only one block will be
executed.

Examples
--------

Testing for a variable::

  <dtml-if snake>
    The snake variable is true
  </dtml-if>

Testing for expression conditions::

  <dtml-if expr="num > 5">
    num is greater than five
  <dtml-elif expr="num < 5">
    num is less than five
  <dtml-else>
    num must be five
  </dtml-if>

See Also
--------

`Python Tutorial If Statements <https://docs.python.org/3/tutorial/controlflow.html#if-statements>`_


in: Loops over sequences
========================

The 'in' tag gives you powerful controls for looping over sequences
and performing batch processing.

Syntax
------

'in' tag syntax::

  <dtml-in SequenceVariable|expr="SequenceExpression">
  [<dtml-else>]
  </dtml-in>

a commenting identifier at the end tag is allowed and will be ignored like::

  </dtml-in my_short_sequ_name>

same for '</dtml-if>' and '</dtml-let>'

The 'in' block is repeated once for each item in the sequence
variable or sequence expression. The current item is pushed on to
the DTML namespace during each executing of the 'in' block.

If there are no items in the sequence variable or expression, the
optional 'else' block is executed.

Attributes
----------

mapping
  Iterates over mapping objects rather than instances. This allows values of
  the mapping objects to be accessed as DTML variables.

reverse
  Reverses the sequence.

sort=string
  Sorts the sequence by the given attribute name.

start=int
  The number of the first item to be shown, where items are numbered from 1.

end=int
  The number of the last item to be shown, where items are numbered from 1.

size=int
  The size of the batch.

skip_unauthorized
  Don't raise an exception if an unauthorized item is encountered.

orphan=int
  The desired minimum batch size. This controls how sequences are split into
  batches. If a batch smaller than the orphan size would occur, then no split
  is performed, and a batch larger than the batch size results.

  For example, if the sequence size is 12, the batch size is 10 the orphan size
  is 3, then the result is one batch with all 12 items since splitting the
  items into two batches would result in a batch smaller than the orphan size.

  The default value is 0.

overlap=int
  The number of items to overlap between batches. The default is no overlap.

previous
  Iterates once if there is a previous batch. Sets batch variables for previous
  sequence.

next
  Iterates once if there is a next batch. Sets batch variables for the next
  sequence.

prefix=string
  Provide versions of the tag variables that start with this prefix instead of
  "sequence", and that use underscores (_) instead of hyphens (-). The prefix
  must start with a letter and contain only alphanumeric characters and
  underscores (_).

sort_expr=expression
  Sorts the sequence by an attribute named by the value of the expression. This
  allows you to sort on different attributes.

reverse_expr=expression
  Reverses the sequence if the expression evaluates to true. This allows you to
  selectively reverse the sequence.

Tag Variables
-------------

Current Item Variables
++++++++++++++++++++++

These variables describe the current item.

sequence-item
  The current item.

sequence-key
  The current key. When looping over tuples of the form '(key,value)', the 'in'
  tag interprets them as '(sequence-key, sequence-item)'.

sequence-index
  The index starting with 0 of the current item.

sequence-number
  The index starting with 1 of the current item.

sequence-roman
  The index in lowercase Roman numerals of the current item.

sequence-Roman
  The index in uppercase Roman numerals of the current item.

sequence-letter
  The index in lowercase letters of the current item.

sequence-Letter
  The index in uppercase letters of the current item.

sequence-start
  True if the current item is the first item.

sequence-end
  True if the current item is the last item.

sequence-even
  True if the index of the current item is even.

sequence-odd
  True if the index of the current item is odd.

sequence-length
  The length of the sequence.

sequence-var-*variable*
  A variable in the current item. For example, 'sequence-var-title' is the
  'title' variable of the current item. Normally you can access these variables
  directly since the current item is pushed on the DTML namespace. However
  these variables can be useful when displaying previous and next batch
  information.

sequence-index-*variable*
  The index of a variable of the current item.

Summary Variables
+++++++++++++++++

These variable summarize information about numeric item variables. To use these
variable you must loop over objects (like database query results) that have
numeric variables.

total-*variable*
  The total of all occurrences of an item variable. 

count-*variable*
  The number of occurrences of an item variable.

min-*variable*
  The minimum value of an item variable.

max-*variable*
  The maximum value of an item variable.

mean-*variable*
  The mean value of an item variable.

variance-*variable*
  The variance of an item variable with count-1 degrees of freedom.

variance-n-*variable*
  The variance of an item variable with n degrees of freedom.

standard-deviation-*variable*
  The standard-deviation of an item variable with count-1 degrees of freedom.

standard-deviation-n-*variable*
  The standard-deviation of an item variable with n degrees of freedom.

Grouping Variables
++++++++++++++++++

These variables allow you to track changes in current item variables.

first-*variable*
  True if the current item is the first with a particular value for a variable.

last-*variable*
  True if the current item is the last with a particular value for a variable.

Batch Variables
+++++++++++++++

sequence-query
  The query string with the 'start' variable removed. You can use this variable
  to construct links to next and previous batches.

sequence-step-size
  The batch size.

previous-sequence
  True if the current batch is not the first one. Note, this variable is only
  true for the first loop iteration.

previous-sequence-start-index
  The starting index of the previous batch.

previous-sequence-start-number
  The starting number of the previous batch. Note, this is the same as
  'previous-sequence-start-index' + 1.

previous-sequence-end-index
  The ending index of the previous batch.

previous-sequence-end-number
  The ending number of the previous batch. Note, this is the same as
  'previous-sequence-end-index' + 1.

previous-sequence-size
  The size of the previous batch.

previous-batches
  A sequence of mapping objects with information about all previous batches.
  Each mapping object has these keys 'batch-start-index', 'batch-end-index',
  and 'batch-size'.

next-sequence
  True if the current batch is not the last batch. Note, this variable is only
  true for the last loop iteration.

next-sequence-start-index
  The starting index of the next sequence.

next-sequence-start-number
  The starting number of the next sequence. Note, this is the same as
  'next-sequence-start-index' + 1.

next-sequence-end-index
  The ending index of the next sequence.

next-sequence-end-number
  The ending number of the next sequence. Note, this is the same as
  'next-sequence-end-index' + 1.

next-sequence-size
  The size of the next index.

next-batches
  A sequence of mapping objects with information about all following batches.
  Each mapping object has these keys 'batch-start-index', 'batch-end-index',
  and 'batch-size'.

Examples
--------

Looping over sub-objects::

  <dtml-in objectValues>
    title: <dtml-var title><br>
  </dtml-in>

Looping over two sets of objects, using prefixes::

  <dtml-let rows="(1,2,3)" cols="(4,5,6)">
    <dtml-in rows prefix="row">
      <dtml-in cols prefix="col">
        <dtml-var expr="row_item * col_item"><br>
        <dtml-if col_end>
          <dtml-var expr="col_total_item * row_mean_item">
        </dtml-if>
      </dtml-in>
    </dtml-in>
  </dtml-let>

Looping over a list of '(key, value)' tuples::

  <dtml-in objectItems>
    id: <dtml-var sequence-key>, title: <dtml-var title><br>
  </dtml-in> 

Creating alternate colored table rows::

  <table>
  <dtml-in objectValues>
  <tr <dtml-if sequence-odd>bgcolor="#EEEEEE"
      <dtml-else>bgcolor="#FFFFFF"
      </dtml-if>>
    <td><dtml-var title></td>
  </tr>
  </dtml-in>
  </table>

Basic batch processing::

  <p>
  <dtml-in largeSequence size=10 start=start previous>
    <a href="<dtml-var absolute_url>
      <dtml-var sequence-query>query_start=<dtml-var previous-sequence-start-number>">
      Previous
    </a>
  </dtml-in>

  <dtml-in largeSequence size=10 start=start next>
    <a href="<dtml-var absolute_url>
      <dtml-var sequence-query>query_start=<dtml-var next-sequence-start-number>">
      Next
    </a>
  </dtml-in>
  </p>

  <p>
  <dtml-in largeSequence size=10 start=start>
    <dtml-var sequence-item>
  </dtml-in>
  </p>

This example creates *Previous* and *Next* links to navigate between batches.
Note, by using 'sequence-query', you do not lose any GET variables as you
navigate between batches.

let: Defines DTML variables
===========================

The 'let' tag defines variables in the DTML namespace.

Syntax
------

'let' tag syntax::

  <dtml-let [Name=Variable][Name="Expression"]...>
  </dtml-let>

The 'let' tag is a block tag. Variables are defined by tag arguments. Defined
variables are pushed onto the DTML namespace while the 'let' block is executed.
Variables are defined by attributes. The 'let' tag can have one or more
attributes with arbitrary names. If the attributes are defined with double
quotes they are considered expressions, otherwise they are looked up by name.
Attributes are processed in order, so later attributes can reference, and/or
overwrite earlier ones.

Examples
--------

Basic usage::

  <dtml-let name="'Bob'" ids=objectIds>
    name: <dtml-var name>
    ids: <dtml-var ids>
  </dtml-let>

Using the 'let' tag with the 'in' tag::

 <dtml-in expr="(1,2,3,4)">
   <dtml-let num=sequence-item
             index=sequence-index
             result="num*index">
     <dtml-var num> * <dtml-var index> = <dtml-var result>
   </dtml-let>
 </dtml-in>

This yields::

  1 * 0 = 0
  2 * 1 = 2
  3 * 2 = 6
  4 * 3 = 12

See Also
--------

- with tag


mime: Formats data with MIME
============================

The 'mime' tag allows you to create MIME encoded data. It is chiefly used to
format email inside the 'sendmail' tag.

Syntax
------

'mime' tag syntax::

  <dtml-mime>
  [<dtml-boundry>]
  ...
  </dtml-mime>

The 'mime' tag is a block tag. The block is can be divided by one or more
'boundry' tags to create a multi-part MIME message. 'mime' tags may be nested.
The 'mime' tag is most often used inside the 'sendmail' tag.

Attributes
----------

Both the 'mime' and 'boundry' tags have the same attributes.

encode=string
  MIME Content-Transfer-Encoding header, defaults to 'base64'. Valid encoding
  options include 'base64', 'quoted-printable', 'uuencode', 'x-uuencode',
  'uue', 'x-uue', and '7bit'. If the 'encode' attribute is set to '7bit' no
  encoding is done on the block and the data is assumed to be in a valid MIME
  format.

type=string
  MIME Content-Type header.

type_expr=string
  MIME Content-Type header as a variable expression. You cannot use both 'type'
  and 'type_expr'.

name=string
  MIME Content-Type header name.

name_expr=string
  MIME Content-Type header name as a variable expression. You cannot use both
  'name' and 'name_expr'.

disposition=string
  MIME Content-Disposition header.

disposition_expr=string
  MIME Content-Disposition header as a variable expression. You cannot use both
  'disposition' and 'disposition_expr'.

filename=string
  MIME Content-Disposition header filename.

filename_expr=string
  MIME Content-Disposition header filename as a variable expression. You cannot
  use both 'filename' and 'filename_expr'.

skip_expr=string
  A variable expression that if true, skips the block. You can use this
  attribute to selectively include MIME blocks.

Examples
--------

Sending a file attachment::

  <dtml-sendmail>
  To: <dtml-var recipient>
  Subject: Resume
  <dtml-mime type="text/plain" encode="7bit">

  Hi, please take a look at my resume.

  <dtml-boundary type="application/octet-stream" disposition="attachment" 
  encode="base64" filename_expr="resume_file.getId()"><dtml-var expr="resume_file.read()"></dtml-mime>
  </dtml-sendmail>

See Also
--------

- `Python Library mimetools <https://docs.python.org/library/mimetools.html>`_

raise: Raises an exception
==========================

The 'raise' tag raises an exception, mirroring the Python 'raise'
statement.

Syntax
------

'raise' tag syntax::

  <dtml-raise ExceptionName|ExceptionExpression>
  </dtml-raise>

The 'raise' tag is a block tag. It raises an exception. Exceptions
can be an exception class or a string. The contents of the tag are
passed as the error value.

Examples
--------

Raising a KeyError::

  <dtml-raise KeyError></dtml-raise>

Raising an HTTP 404 error::

  <dtml-raise NotFound>Web Page Not Found</dtml-raise>

See Also
--------

- try tag

- `Python Tutorial Errors and Exceptions <https://docs.python.org/tutorial/errors.html>`_

- `Python Built-in Exceptions <https://docs.python.org/library/exceptions.html>`_

return: Returns data
====================

The 'return' tag stops executing DTML and returns data. It mirrors
the Python 'return' statement.

Syntax
------

'return' tag syntax::

  <dtml-return ReturnVariable|expr="ReturnExpression">

Stops execution of DTML and returns a variable or expression. The
DTML output is not returned. Usually a return expression is more
useful than a return variable. Scripts largely obsolete this tag.

Examples

Returning a variable::

  <dtml-return result>

Returning a Python dictionary::

  <dtml-return expr="{'hi':200, 'lo':5}">

sendmail: Sends email with SMTP
===============================

The 'sendmail' tag sends an email message using SMTP.

Syntax
------

'sendmail' tag syntax::

  <dtml-sendmail>
  </dtml-sendmail>

The 'sendmail' tag is a block tag. It either requires a 'mailhost' or a
'smtphost' argument, but not both. The tag block is sent as an email message.
The beginning of the block describes the email headers. The headers are
separated from the body by a blank line. Alternately the 'To', 'From' and
'Subject' headers can be set with tag arguments.

Attributes
----------

mailhost
  The name of a Zope MailHost object to use to send email. You cannot specify
  both a mailhost and a smtphost.

smtphost
  The name of a SMTP server used to send email. You cannot specify both a
  mailhost and a smtphost.

port
  If the smtphost attribute is used, then the port attribute is used to specify
  a port number to connect to. If not specified, then port 25 will be used.

mailto
  The recipient address or a list of recipient addresses separated by commas.
  This can also be specified with the 'To' header.

mailfrom
  The sender address. This can also be specified with the 'From' header.

subject
  The email subject. This can also be specified with the 'Subject' header.

Examples
--------

Sending an email message using a Mail Host::

  <dtml-sendmail mailhost="mailhost">
  To: <dtml-var recipient>
  From: <dtml-var sender>
  Subject: <dtml-var subject>

  Dear <dtml-var recipient>,

  You order number <dtml-var order_number> is ready.
  Please pick it up at your soonest convenience.
  </dtml-sendmail>

See Also
--------

- `RFC 821 (SMTP Protocol) <https://www.ietf.org/rfc/rfc0821.txt>`_

- mime tag


sqlgroup: Formats complex SQL expressions
=========================================

The 'sqlgroup' tag formats complex boolean SQL expressions. You can use it
along with the 'sqltest' tag to build dynamic SQL queries that tailor
themselves to the environment. This tag is used in SQL Methods.

Syntax
------

'sqlgroup' tag syntax::

  <dtml-sqlgroup>
  [<dtml-or>]
  [<dtml-and>]
  ...
  </dtml-sqlgroup>

The 'sqlgroup' tag is a block tag. It is divided into blocks with
one or more optional 'or' and 'and' tags. 'sqlgroup' tags can be
nested to produce complex logic.

Attributes
----------

required=boolean
  Indicates whether the group is required. If it is not required and contains
  nothing, it is excluded from the DTML output.

where=boolean
  If true, includes the string "where". This is useful for the outermost
  'sqlgroup' tag in a SQL 'select' query.

Examples
--------

Sample usage::

  select * from employees 
  <dtml-sqlgroup where>
    <dtml-sqltest salary op="gt" type="float" optional>
  <dtml-and>
    <dtml-sqltest first type="nb" multiple optional>
  <dtml-and>
    <dtml-sqltest last type="nb" multiple optional>
  </dtml-sqlgroup>  

If 'first' is 'Bob' and 'last' is 'Smith, McDonald' it renders::

  select * from employees
  where
  (first='Bob'
   and
   last in ('Smith', 'McDonald')
  )

If 'salary' is 50000 and 'last' is 'Smith' it renders::

  select * from employees
  where 
  (salary > 50000.0
   and
   last='Smith'
  )

Nested 'sqlgroup' tags::

  select * from employees
  <dtml-sqlgroup where>
    <dtml-sqlgroup>
       <dtml-sqltest first op="like" type="nb">
    <dtml-and>
       <dtml-sqltest last op="like" type="nb">
    </dtml-sqlgroup>
  <dtml-or>
    <dtml-sqltest salary op="gt" type="float">
  </dtml-sqlgroup>

Given sample arguments, this template renders to SQL like so::

  select * form employees
  where
  (
    (
     name like 'A*'
     and
     last like 'Smith'
     )
   or
   salary > 20000.0
  )

See Also
--------

- sqltest tag


sqltest: Formats SQL condition tests
====================================

The 'sqltest' tag inserts a condition test into SQL code. It tests a column
against a variable. This tag is used in SQL Methods.

Syntax
------

'sqltest' tag syntax::

  <dtml-sqltest Variable|expr="VariableExpression">

The 'sqltest' tag is a singleton. It inserts a SQL condition test statement. It
is used to build SQL queries. The 'sqltest' tag correctly escapes the inserted
variable. The named variable or variable expression is tested against a SQL
column using the specified comparison operation.

Attributes
----------

type=string
  The type of the variable. Valid types include: 'string', 'int', 'float' and
  'nb'. 'nb' means non-blank string, and should be used instead of 'string'
  unless you want to test for blank values. The type attribute is required and
  is used to properly escape inserted variable.

column=string
  The name of the SQL column to test against. This attribute defaults to the
  variable name.

multiple=boolean
  If true, then the variable may be a sequence of values to test the column
  against.

optional=boolean
  If true, then the test is optional and will not be rendered if the variable
  is empty or non-existent.

op=string
  The comparison operation. Valid comparisons include: 

  eq
    equal to

  gt
    greater than

  lt
    less than

  ne
    not equal to

  ge
    greater than or equal to

  le
    less than or equal to

  The comparison defaults to equal to. If the comparison is not
  recognized it is used anyway. Thus you can use comparisons such
  as 'like'.

Examples
--------

Basic usage::

  select * from employees
    where <dtml-sqltest name type="nb">

If the 'name' variable is 'Bob' then this renders::

  select * from employees
    where name = 'Bob'

Multiple values::

  select * from employees
    where <dtml-sqltest empid type=int multiple>

If the 'empid' variable is '(12,14,17)' then this renders::

  select * from employees
    where empid in (12, 14, 17)

See Also
--------

- sqlgroup tag

- sqlvar tag


sqlvar: Inserts SQL variables
=============================

The 'sqlvar' tag safely inserts variables into SQL code. This tag is used in
SQL Methods.

Syntax
------

'sqlvar' tag syntax::

  <dtml-sqlvar Variable|expr="VariableExpression">

The 'sqlvar' tag is a singleton. Like the 'var' tag, the 'sqlvar' tag looks up
a variable and inserts it. Unlike the var tag, the formatting options are
tailored for SQL code.

Attributes
----------

type=string
  The type of the variable. Valid types include: 'string', 'int', 'float' and
  'nb'. 'nb' means non-blank string and should be used in place of 'string'
  unless you want to use blank strings. The type attribute is required and is
  used to properly escape inserted variable.

optional=boolean
  If true and the variable is null or non-existent, then nothing is inserted.

Examples
--------

Basic usage::

  select * from employees 
    where name=<dtml-sqlvar name type="nb">

This SQL quotes the 'name' string variable.

See Also
--------

- sqltest tag


tree: Inserts a tree widget
===========================

The 'tree' tag displays a dynamic tree widget by querying Zope objects.

Syntax
------

'tree' tag syntax::

  <dtml-tree [VariableName|expr="VariableExpression"]>
  </dtml-tree>

The 'tree' tag is a block tag. It renders a dynamic tree widget in
HTML. The root of the tree is given by variable name or
expression, if present, otherwise it defaults to the current
object. The 'tree' block is rendered for each tree node, with the
current node pushed onto the DTML namespace.

Tree state is set in HTTP cookies. Thus for trees to work, cookies
must be enabled. Also you can only have one tree per page.

Attributes
----------

branches=string
  Finds tree branches by calling the named method. The default method is
  'tpValues' which most Zope objects support.

branches_expr=string
  Finds tree branches by evaluating the expression.

id=string
  The name of a method or id to determine tree state. It defaults to 'tpId'
  which most Zope objects support. This attribute is for advanced usage only.

url=string
  The name of a method or attribute to determine tree item URLs. It defaults to
  'tpURL' which most Zope objects support. This attribute is for advanced usage
  only.

leaves=string
  The name of a DTML Document or Method used to render nodes that don't have
  any children. Note: this document should begin with '<dtml-var
  standard_html_header>' and end with '<dtml-var standard_html_footer>' in
  order to ensure proper display in the tree.

header=string
  The name of a DTML Document or Method displayed before expanded nodes. If the
  header is not found, it is skipped.

footer=string
  The name of a DTML Document or Method displayed after expanded nodes. If the
  footer is not found, it is skipped.

nowrap=boolean
  If true then rather than wrap, nodes may be truncated to fit available space.

sort=string
  Sorts the branches by the named attribute.

reverse
  Reverses the order of the branches.

assume_children=boolean
  Assumes that nodes have children. This is useful if fetching and querying
  child nodes is a costly process. This results in plus boxes being drawn next
  to all nodes.

single=boolean
  Allows only one branch to be expanded at a time. When you expand a new
  branch, any other expanded branches close.

skip_unauthorized
  Skips nodes that the user is unauthorized to see, rather than raising an
  error.

urlparam=string
  A query string which is included in the expanding and contracting widget
  links. This attribute is for advanced usage only.

prefix=string
  Provide versions of the tag variables that start with this prefix instead of
  "tree", and that use underscores (_) instead of hyphens (-). The prefix must
  start with a letter and contain only alphanumeric characters and underscores
  (_).

Tag Variables
-------------

tree-item-expanded
  True if the current node is expanded.

tree-item-url
  The URL of the current node.

tree-root-url
  The URL of the root node.

tree-level
  The depth of the current node. Top-level nodes have a depth of zero.

tree-colspan
  The number of levels deep the tree is being rendered. This variable along
  with the 'tree-level' variable can be used to calculate table rows and
  colspan settings when inserting table rows into the tree table.

tree-state
  The tree state expressed as a list of ids and sub-lists of ids. This variable
  is for advanced usage only.

Tag Control Variables
---------------------

You can control the tree tag by setting these variables.

expand_all
  If this variable is true then the entire tree is expanded.

collapse_all
  If this variable is true then the entire tree is collapsed.

Examples
--------

Display a tree rooted in the current object::

  <dtml-tree>
    <dtml-var title_or_id>
  </dtml-tree>

Display a tree rooted in another object, using a custom branches
method::

  <dtml-tree expr="folder.object" branches="objectValues">
    Node id : <dtml-var getId>
  </dtml-tree>

try: Handles exceptions
=======================

The 'try' tag allows exception handling in DTML, mirroring the Python
'try/except' and 'try/finally' constructs.

Syntax
------

The 'try' tag has two different syntaxes, 'try/except/else' and 'try/finally'.

'try/except/else' Syntax::

  <dtml-try>
  <dtml-except [ExceptionName] [ExceptionName]...>
  ... 
  [<dtml-else>]
  </dtml-try>

The 'try' tag encloses a block in which exceptions can be caught and handled.
There can be one or more 'except' tags that handles zero or more exceptions. If
an 'except' tag does not specify an exception, then it handles all exceptions.

When an exception is raised, control jumps to the first 'except' tag that
handles the exception. If there is no 'except' tag to handle the exception,
then the exception is raised normally.

If no exception is raised, and there is an 'else' tag, then the 'else' tag will
be executed after the body of the 'try' tag.

The 'except' and 'else' tags are optional.

'try/finally' Syntax::

  <dtml-try>
  <dtml-finally>
  </dtml-try>

The 'finally' tag cannot be used in the same 'try' block as the 'except' and
'else' tags. If there is a 'finally' tag, its block will be executed whether or
not an exception is raised in the 'try' block.

Attributes
----------

except
  Zero or more exception names. If no exceptions are listed then the except tag
  will handle all exceptions.

Tag Variables
-------------

Inside the 'except' block these variables are defined.

error_type
  The exception type.

error_value
  The exception value.

error_tb
  The traceback.

Examples
--------

Catching a math error::

  <dtml-try>
  <dtml-var expr="1/0">
  <dtml-except ZeroDivisionError>
  You tried to divide by zero.
  </dtml-try>

Returning information about the handled exception::

  <dtml-try>
  <dtml-call dangerousMethod>
  <dtml-except>
  An error occurred.
  Error type: <dtml-var error_type>
  Error value: <dtml-var error_value>
  </dtml-try>

Using finally to make sure to perform clean up regardless of whether an error
is raised or not::

  <dtml-call acquireLock>
  <dtml-try>
  <dtml-call someMethod>
  <dtml-finally>
  <dtml-call releaseLock>
  </dtml-try>

See Also
--------

- raise tag

- `Python Tutorial Errors and Exceptions <https://docs.python.org/tutorial/errors.html>`_

- `Python Built-in Exceptions <https://docs.python.org/library/exceptions.html>`_


unless: Tests a condition
=========================

The 'unless' tag provides a shortcut for testing negative conditions. For more
complete condition testing use the 'if' tag.

Syntax
------

'unless' tag syntax::

  <dtml-unless ConditionVariable|expr="ConditionExpression">
  </dtml-unless>

The 'unless' tag is a block tag. If the condition variable or expression
evaluates to false, then the contained block is executed. Like the 'if' tag,
variables that are not present are considered false.

Examples
--------

Testing a variable::

  <dtml-unless testMode>
    <dtml-call dangerousOperation>
  </dtml-unless>

The block will be executed if 'testMode' does not exist, or exists but is
false.

See Also
--------

- if tag


var: Inserts a variable
=======================

The 'var' tags allows you insert variables into DTML output.

Syntax
------

'var' tag syntax::

  <dtml-var Variable|expr="Expression">

The 'var' tag is a singleton tag. The 'var' tag finds a variable by searching
the DTML namespace which usually consists of current object, the current
object's containers, and finally the web request. If the variable is found, it
is inserted into the DTML output. If not found, Zope raises an error.

'var' tag entity syntax::

  &dtml-variableName;

Entity syntax is a short cut which inserts and HTML quotes the variable. It is
useful when inserting variables into HTML tags.

'var' tag entity syntax with attributes::

  &dtml.attribute1[.attribute2]...-variableName;

To a limited degree you may specify attributes with the entity syntax. You may
include zero or more attributes delimited by periods. You cannot provide
arguments for attributes using the entity syntax. If you provide zero or more
attributes, then the variable is not automatically HTML quoted. Thus you can
avoid HTML quoting with this syntax, '&dtml.-variableName;'.

Attributes
----------

html_quote
  Convert characters that have special meaning in HTML to HTML character
  entities.

missing=string
  Specify a default value in case Zope cannot find the variable.

fmt=string
  Format a variable. Zope provides a few built-in formats including C-style
  format strings. For more information on C-style format strings see the
  `Python Library Reference <https://docs.python.org/library/stdtypes.html#typesseq-strings>`_.
  If the format string is not a built-in format, then it is assumed to be a
  method of the object, and it called.

  collection-length
    The length of the variable, assuming it is a sequence.

null=string
  A default value to use if the variable is None.

lower
  Converts upper-case letters to lower case. 

upper
  Converts lower-case letters to upper case. 

capitalize
  Capitalizes the first character of the inserted word.

spacify
  Changes underscores in the inserted value to spaces.

thousands_commas
  Inserts commas every three digits to the left of a decimal point in values
  containing numbers for example '12000' becomes '12,000'.

url
  Inserts the URL of the object, by calling its 'absolute_url' method.

url_quote
  Converts characters that have special meaning in URLs to HTML character
  entities.

url_quote_plus
  URL quotes character, like 'url_quote' but also converts spaces to plus
  signs.

sql_quote
  Converts single quotes to pairs of single quotes. This is needed to safely
  include values in SQL strings.

newline_to_br
  Convert newlines (including carriage returns) to HTML break tags.

size=arg
  Truncates the variable at the given length (Note: if a space occurs in the
  second half of the truncated string, then the string is further truncated to
  the right-most space).

etc=arg
  Specifies a string to add to the end of a string which has been truncated (by
  setting the 'size' attribute listed above). By default, this is '...'


Examples
--------

Inserting a simple variable into a document::

  <dtml-var standard_html_header>

Truncation::

  <dtml-var colors size=10 etc=", etc.">

will produce the following output if *colors* is the string 'red yellow
green'::

  red yellow, etc.

C-style string formatting::

  <dtml-var expr="23432.2323" fmt="%.2f">

renders to::

  23432.23

Inserting a variable, *link*, inside an HTML 'A' tag with the entity syntax::

  <a href="&dtml-link;">Link</a>

Inserting a link to a document 'doc', using entity syntax with attributes::

  <a href="&dtml.url-doc;"><dtml-var doc fmt="title_or_id"></a>

This creates an HTML link to an object using its URL and title. This example
calls the object's 'absolute_url' method for the URL (using the 'url'
attribute) and its 'title_or_id' method for the title.

with: Controls DTML variable look up
====================================

The 'with' tag pushes an object onto the DTML namespace. Variables will be
looked up in the pushed object first.

Syntax
------

'with' tag syntax::

  <dtml-with Variable|expr="Expression">
  </dtml-with>

The 'with' tag is a block tag. It pushes the named variable or variable
expression onto the DTML namespace for the duration of the 'with' block. Thus
names are looked up in the pushed object first.

Attributes
----------

only
  Limits the DTML namespace to only include the one defined in the 'with' tag.

mapping
  Indicates that the variable or expression is a mapping object. This ensures
  that variables are looked up correctly in the mapping object.

Examples
--------

Looking up a variable in the REQUEST::

  <dtml-with REQUEST only>
    <dtml-if id>
      <dtml-var id>
    <dtml-else>
      'id' was not in the request.
    </dtml-if>
  </dtml-with>

Pushing the first child on the DTML namespace::

  <dtml-with expr="objectValues()[0]">
    First child's id: <dtml-var id>
  </dtml-with>

See Also
--------

- let tag
