Appendix C: Zope Page Templates Reference
#########################################

Zope Page Templates are an HTML/XML generation tool. This appendix is a
reference to Zope Page Templates standards: Template Attribute Language (TAL),
TAL Expression Syntax (TALES), and Macro Expansion TAL (METAL). It also
describes some ZPT-specific behaviors that are not part of the standards.

TAL Overview
============

The *Template Attribute Language* (TAL) standard is an attribute language used
to create dynamic templates. It allows elements of a document to be replaced,
repeated, or omitted.

The statements of TAL are XML attributes from the TAL namespace. These
attributes can be applied to an XML or HTML document in order to make it act as
a template.

A **TAL statement** has a name (the attribute name) and a body (the attribute
value). For example, a ``content`` statement might look like::

  tal:content="string:Hello"

The element on which a statement is defined is its **statement element**. Most
TAL statements require expressions, but the syntax and semantics of these
expressions are not part of TAL. TALES is recommended for this purpose.

TAL Namespace
+++++++++++++

The TAL namespace URI and recommended alias are currently defined
as::

  xmlns:tal="http://xml.zope.org/namespaces/tal"

This is not a URL, but merely a unique identifier. Do not expect a browser to
resolve it successfully.

Zope does not require an XML namespace declaration when creating templates with
a content-type of ``text/html``. However, it does require an XML namespace
declaration for all other content-types.

TAL Statements
++++++++++++++

These are the tal statements:

- tal:attributes - dynamically change element attributes.

- tal:define - define variables.

- tal:switch - define a switch condition

- tal:condition - test conditions.

- tal:case - include element only if expression is equal to parent switch

- tal:content - replace the content of an element.

- tal:omit-tag - remove an element, leaving the content of the element.

- tal:on-error - handle errors.

- tal:repeat - repeat an element.

- tal:replace - replace the content of an element and remove the element
  leaving the content.

Expressions used in statements may return values of any type, although most
statements will only accept strings, or will convert values into a string
representation. The expression language must define a value named *nothing*
that is not a string. In particular, this value is useful for deleting elements
or attributes.

Order of Operations
+++++++++++++++++++

When there is only one TAL statement per element, the order in which they are
executed is simple. Starting with the root element, each element's statements
are executed, then each of its child elements is visited, in order, to do the
same.

Any combination of statements may appear on the same elements, except that the
``content`` and ``replace`` statements may not appear together.

Due to the fact that TAL sees statements as XML attributes, even in HTML
documents, it cannot use the order in which statements are written in the tag
to determine the order in which they are executed. TAL must also forbid
multiples of the same kind of statement on a single element, so it is
sufficient to arrange the kinds of statement in a precedence list.

When an element has multiple statements, they are executed in this order:


1. define

2. switch

3. condition

4. repeat

5. case

6. content or replace

7. attributes

8. omit-tag

Since the ``on-error`` statement is only invoked when an error occurs, it does
not appear in the list.

It may not be apparent that there needs to be an ordering. The reason that
there must be one is that TAL is XML based. The XML specification specifically
states that XML processors are free to rewrite the terms. In particular, you
cannot assume that attributes of an XML statement will be processed in the
order written, particularly if there is another preprocessor involved. To avoid
needless proliferation of tags, and still permit unambiguous execution of
complex TAL, a precedence order was chosen according to the following
rationale.

The reasoning behind this ordering goes like this: You often want to set up
variables for use in other statements, so ``define`` comes first. Then any
switch statement. The very next thing to do is decide whether this element
will be included at all, so ``condition`` is next; since the condition may depend
on variables you just set, it comes after ``define``. It is valuable be able to
replace various parts of an element with different values on each iteration of
a repeat, so ``repeat`` is next, followed by ``case``. It makes no sense to
replace attributes and then throw them away, so ``attributes`` is last. The
remaining statements clash, because they each replace or edit the statement
element.

attributes: Replace element attributes
======================================

Syntax
++++++

tal:attributes syntax::

  argument             ::= attribute_statement [';' attribute_statement]*
  attribute_statement  ::= attribute_name expression
  attribute_name       ::= [namespace-prefix ':'] Name
  namespace-prefix     ::= Name

*Note: If you want to include a semi-colon (;) in an `expression`, it must be
escaped by doubling it (;;).*

Description
+++++++++++

The ``tal:attributes`` statement replaces the value of an attribute (or creates
an attribute) with a dynamic value. You can qualify an attribute name with a
namespace prefix, for example::

  html:table

if you are generating an XML document with multiple namespaces. The value of
each expression is converted to a string, if necessary.

If the expression associated with an attribute assignment evaluates to
*nothing*, then that attribute is deleted from the statement element. If the
expression evaluates to *default*, then that attribute is left unchanged. Each
attribute assignment is independent, so attributes may be assigned in the same
statement in which some attributes are deleted and others are left alone.

If you use ``tal:attributes`` on an element with an active ``tal:replace``
command, the ``tal:attributes`` statement is ignored.


If you use ``tal:attributes`` on an element with a ``tal:repeat`` statement, the
replacement is made on each repetition of the element, and the replacement
expression is evaluated fresh for each repetition.

Examples
++++++++

Replacing a link::

  <a href="/sample/link.html"
     tal:attributes="href context/sub/absolute_url">

Replacing two attributes::

  <textarea
    rows="80" cols="20"
    tal:attributes="rows request/rows;cols request/cols">

condition: Conditionally insert or remove an element
====================================================

Syntax
++++++

tal:condition syntax::

  argument ::= expression

Description
+++++++++++

The ``tal:condition`` statement includes the statement element in the template
only if the condition is met, and omits it otherwise. If its expression
evaluates to a *true* value, then normal processing of the element continues,
otherwise the statement element is immediately removed from the template. For
these purposes, the value *nothing* is false, and *default* has the same effect
as returning a true value.

*Note: Zope considers missing variables, None, zero, empty strings, and empty
sequences false; all other values are true.*

Examples
++++++++

Test a variable before inserting it (the first example tests for existence and
truth, while the second only tests for existence)::

  <p tal:condition="request/message | nothing"
     tal:content="request/message">message goes here</p>

  <p tal:condition="exists:request/message"
     tal:content="request/message">message goes here</p>

Test for alternate conditions::

  <div tal:repeat="item python:range(10)">
    <p tal:condition="repeat/item/even">Even</p>
    <p tal:condition="repeat/item/odd">Odd</p>
  </div>

content: Replace the content of an element
==========================================

Syntax
++++++

tal:content syntax::

  argument ::= (['text'] | 'structure') expression

Description
+++++++++++

Rather than replacing an entire element, you can insert text or structure in
place of its children with the ``tal:content`` statement. The statement argument
is exactly like that of ``tal:replace``, and is interpreted in the same fashion.
If the expression evaluates to *nothing*, the statement element is left
childless. If the expression evaluates to *default*, then the element's
contents are unchanged.

The default replacement behavior is ``text``, which replaces angle-brackets and
ampersands with their HTML entity equivalents. The ``structure`` keyword passes
the replacement text through unchanged, allowing HTML/XML markup to be
inserted. This can break your page if the text contains unanticipated markup
(e.g.. text submitted via a web form), which is the reason that it is not the
default.

Examples
++++++++

Inserting the user name::

  <p tal:content="user/getUserName">Fred Farkas</p>

Inserting HTML/XML::

  <p tal:content="structure context/getStory">
    marked <b>up</b> content goes here.
  </p>

define: Define variables
========================

Syntax
++++++

tal:define syntax::

  argument       ::= define_scope [';' define_scope]*
  define_scope   ::= (['local'] | 'global') define_var
  define_var     ::= variable_name expression
  variable_name  ::= Name

*Note: If you want to include a semi-colon (;) in an `expression`, it must be
escaped by doubling it (;;).*

Description
+++++++++++

The ``tal:define`` statement defines variables. You can define two different
kinds of TAL variables: local and global. When you define a local variable in a
statement element, you can only use that variable in that element and the
elements it contains. If you redefine a local variable in a contained element,
the new definition hides the outer element's definition within the inner
element. When you define a global variables, you can use it in any element
processed after the defining element. If you redefine a global variable, you
replace its definition for the rest of the template.

*Note: local variables are the default*

If the expression associated with a variable evaluates to *nothing*, then that
variable has the value *nothing*, and may be used as such in further
expressions. Likewise, if the expression evaluates to *default*, then the
variable has the value *default*, and may be used as such in further
expressions.

Examples
++++++++

Defining a global variable::

  tal:define="global company_name string:Zope Corp, Inc."

Defining two variables, where the second depends on the first::

  tal:define="mytitle template/title; tlen python:len(mytitle)"


switch and case: Set up a switch statement
==========================================

Defines a switch clause.

::

  <ul tal:switch="len(items) % 2">
    <li tal:case="True">odd</li>
    <li tal:case="False">even</li>
  </ul>

Syntax
++++++

``tal:case`` and ``tal:switch`` syntax::

    argument ::= expression

Description
+++++++++++

The *switch* and *case* construct is a short-hand syntax for matching
a set of expressions against a single parent.

The ``tal:switch`` statement is used to set a new parent expression
and the contained ``tal:case`` statements are then matched in sequence
such that only the first match succeeds.

Note that the symbol ``default`` affirms the case precisely when no
previous case has been successful. It should therefore be placed last.

Examples
++++++++

::

  <ul tal:switch="item/type">
    <li tal:case="string:document">
      Document
    </li>
    <li tal:case="string:folder">
      Folder
    </li>
    <li tal:case="default">
      Other
    </li>
  </ul>


omit-tag: Remove an element, leaving its contents
=================================================

Syntax
++++++

tal:omit-tag syntax::

  argument ::= [ expression ]

Description
+++++++++++

The ``tal:omit-tag`` statement leaves the contents of an element in place while
omitting the surrounding start and end tags.

If the expression evaluates to a *false* value, then normal processing of the
element continues and the tags are not omitted. If the expression evaluates to
a *true* value, or no expression is provided, the statement element is replaced
with its contents.

Zope treats empty strings, empty sequences, zero, None, and *nothing* as false.
All other values are considered true, including *default*.

Examples
++++++++

Unconditionally omitting a tag::

  <div tal:omit-tag="" comment="This tag will be removed">
    <i>...but this text will remain.</i>
  </div>

Conditionally omitting a tag::

  <b tal:omit-tag="not:bold">
    I may be bold.
  </b>

The above example will omit the ``b`` tag if the variable ``bold`` is false.

Creating ten paragraph tags, with no enclosing tag::

  <span tal:repeat="n python:range(10)"
        tal:omit-tag="">
    <p tal:content="n">1</p>
  </span>


on-error: Handle errors
=======================

Syntax
++++++

tal:on-error syntax::

  argument ::= (['text'] | 'structure') expression

Description
+++++++++++

The ``tal:on-error`` statement provides error handling for your template. When a
TAL statement produces an error, the TAL interpreter searches for a
``tal:on-error`` statement on the same element, then on the enclosing element,
and so forth. The first ``tal:on-error`` found is invoked. It is treated as a
``tal:content`` statement.

A local variable ``error`` is set. This variable has these attributes:

type
  the exception type

value
  the exception instance

traceback
  the traceback object

The simplest sort of ``tal:on-error`` statement has a literal error string or
*nothing* for an expression. A more complex handler may call a script that
examines the error and either emits error text or raises an exception to
propagate the error outwards.

Examples
++++++++

Simple error message::

  <b tal:on-error="string: Username is not defined!" 
     tal:content="context/getUsername">Ishmael</b>

Removing elements with errors::

  <b tal:on-error="nothing"
     tal:content="context/getUsername">Ishmael</b>

Calling an error-handling script::

  <div tal:on-error="structure context/errorScript">
  ...
  </div>

Here's what the error-handling script might look like::

  ## Script (Python) "errHandler"
  ##bind namespace=_
  ##
  error=_['error']
  if error.type==ZeroDivisionError:
      return "<p>Can't divide by zero.</p>"
  else
      return """<p>An error ocurred.</p>
      <p>Error type: %s</p>
      <p>Error value: %s</p>""" % (error.type, error.value)


repeat: Repeat an element
=========================

Syntax
++++++

tal:repeat syntax::

  argument      ::= variable_name expression
  variable_name ::= Name

Description
+++++++++++

The ``tal:repeat`` statement replicates a sub-tree of your document once for each
item in a sequence. The expression should evaluate to a sequence. If the
sequence is empty, then the statement element is deleted, otherwise it is
repeated for each value in the sequence. If the expression is *default*, then
the element is left unchanged, and no new variables are defined.

The ``variable_name`` is used to define a local variable and a repeat variable.
For each repetition, the local variable is set to the current sequence element,
and the repeat variable is set to an iteration object.

Repeat Variables
++++++++++++++++

You use repeat variables to access information about the current repetition
(such as the repeat index). The repeat variable has the same name as the local
variable, but is only accessible through the built-in variable named ``repeat``.


The following information is available from the repeat variable:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- *index*- - repetition number, starting from zero.

- *number*- - repetition number, starting from one.

- *even*- - true for even-indexed repetitions (0, 2, 4, ...).

- *odd*- - true for odd-indexed repetitions (1, 3, 5, ...).

- *start*- - true for the starting repetition (index 0).

- *end*- - true for the ending, or final, repetition.

- *first*- - true for the first item in a group - see note below

- *last*- - true for the last item in a group - see note below

- *length*- - length of the sequence, which will be the total number of
  repetitions - unsafe, see note below

- *letter*- - repetition number as a lower-case letter: "a" - "z", "aa" - "az",
  "ba" - "bz", ..., "za" - "zz", "aaa" - "aaz", and so forth.

- *Letter*- - upper-case version of - *letter*- .

- *roman*- - repetition number as a lower-case roman numeral: "i", "ii", "iii",
  "iv", "v", etc.

- *Roman*- - upper-case version of - *roman*- .

You can access the contents of the repeat variable using path expressions or
Python expressions. In path expressions, you write a three-part path consisting
of the name ``repeat``, the statement variable's name, and the name of the
information you want, for example, ``repeat/item/start``. In Python expressions,
you use normal dictionary notation to get the repeat variable, then attribute
access to get the information, for example, ``python:repeat['item'].start``.

With the exception of ``start``, ``end``, and ``index``, all of the attributes
of a repeat variable are methods. Thus, when you use a Python expression to
access them, you must call them, as in ``python:repeat['item'].length()``.

The ``length`` attrubute will lead to a page error if the sequence that is
being iterated has no ``len`` method, thus it is somewhat unsafe to use.

Note that ``first`` and ``last`` are intended for use with sorted sequences. They
try to divide the sequence into group of items with the same value. If you
provide a path, then the value obtained by following that path from a sequence
item is used for grouping, otherwise the value of the item is used. You can
provide the path by passing it as a parameter, as in::

  python:repeat['item'].first(color)
  
or by appending it to the path from the repeat variable, as in
``repeat/item/first/color``.

Examples
++++++++

Iterating over a sequence of strings::

  <p tal:repeat="txt python: ('one', 'two', 'three')">
    <span tal:replace="txt" />
  </p>

Inserting a sequence of table rows, and using the repeat variable to number the
rows::

  <table>
    <tr tal:repeat="item context/cart">
      <td tal:content="repeat/item/number">1</td>
      <td tal:content="item/description">Widget</td>
      <td tal:content="item/price">$1.50</td>
    </tr>
  </table>

Nested repeats::

  <table border="1">
    <tr tal:repeat="row python:range(10)">
      <td tal:repeat="column python:range(10)">
        <span tal:define="x repeat/row/number; 
                          y repeat/column/number; 
                          z python:x*y"
              tal:replace="string:$x * $y = $z">
            1 * 1 = 1
        </span>
      </td>
    </tr>
  </table>


Insert objects. Separate groups of objects by meta-type by drawing a rule
between them::

  <div tal:repeat="object objects">
    <h2 tal:condition="repeat/object/first/meta_type"
        tal:content="object/meta_type">Meta Type</h2>
    <p tal:content="object/getId">Object ID</p>
    <hr tal:condition="repeat/object/last/meta_type" />
  </div>

Note, the objects in the above example should already be sorted by meta-type.

replace: Replace an element
===========================

Syntax
++++++

tal:replace syntax::

  argument ::= (['text'] | 'structure') expression

Description
+++++++++++

The ``tal:replace`` statement replaces an element with dynamic content. It
replaces the statement element with either text or a structure (unescaped
markup). The body of the statement is an expression with an optional type
prefix. The value of the expression is converted into an escaped string if you
prefix the expression with ``text`` or omit the prefix, and is inserted unchanged
if you prefix it with ``structure``. Escaping consists of converting ``&amp;`` to
``&amp;amp;``, ``&lt;`` to ``&amp;lt;``, and ``&gt;`` to ``&amp;gt;``.

If the value is *nothing*, then the element is simply removed. If the value is
*default*, then the element is left unchanged.

Examples
++++++++

The two ways to insert the title of a template::

  <span tal:replace="template/title">Title</span>
  <span tal:replace="text template/title">Title</span>

Inserting HTML/XML::

  <div tal:replace="structure table" />

Inserting nothing::

  <div tal:replace="nothing">
    This element is a comment.
  </div>

TALES Overview
==============

The *Template Attribute Language Expression Syntax* (TALES) standard describes
expressions that supply TAL and METAL with data. TALES is *one* possible
expression syntax for these languages, but they are not bound to this
definition. Similarly, TALES could be used in a context having nothing to do
with TAL or METAL.

TALES expressions are described below with any delimiter or quote markup from
higher language layers removed. Here is the basic definition of TALES syntax::

  Expression  ::= [type_prefix ':'] String
  type_prefix ::= Name

Here are some simple examples::

  a/b/c
  path:a/b/c
  nothing
  path:nothing
  python: 1 + 2
  string:Hello, ${user/getUserName}

The optional *type prefix* determines the semantics and syntax of the
*expression string* that follows it. A given implementation of TALES can define
any number of expression types, with whatever syntax you like. It also
determines which expression type is indicated by omitting the prefix.

If you do not specify a prefix, Zope assumes that the expression is a *path*
expression.

TALES Expression Types
++++++++++++++++++++++

These are the TALES expression types supported by Zope:

- path expressions - locate a value by its path.

- exists expressions - test whether a path is valid.

- nocall expressions - locate an object by its path.

- not expressions - negate an expression

- string expressions - format a string

- python expressions - execute a Python expression

Built-in Names
++++++++++++++

These are the names always available to TALES expressions in Zope:

- *nothing*- - special value used by to represent a - *non-value*- (e.g. void,
  None, Nil, NULL).

- *default*- - special value used to specify that existing text should not be
  replaced. See the documentation for individual TAL statements for details on
  how they interpret - *default*- .

- *options*- - the - *keyword*- arguments passed to the template. These are
  generally available when a template is called from Methods and Scripts,
  rather than from the web.

- *repeat*- - the repeat variables; see the ``tal:repeat`` documentation.

- *attrs*- - a dictionary containing the initial values of the attributes of
  the current statement tag.

- *root*- - the system's top-most object: the Zope root folder.

- *context*- - the object to which the template is being applied.

- *container*- - The folder in which the template is located.

- *template*- - the template itself.

- *request*- - the publishing request object.

- *user*- - the authenticated user object.

- *modules*- - a collection through which Python modules and packages can be
  accessed. Only modules which are approved by the Zope security policy can be
  accessed.

Note the names ``root``, ``context``, ``container``, ``template``, ``request``,
``user``, and ``modules`` are optional names supported by Zope, but are not
required by the TALES standard.

Note that the (popular) ``chameleon`` template engine implements ``attrs``
and ``default`` not as standard variables but in a special way.
Trying to change their value may have undefined effects.

Besides variables you can use ``CONTEXTS``
as initial element in a path expression. Its value is a mapping
from predefined variable names to their value. This can be used to
access the predefined variable when it is hidden by a user defined
definition for its name. Again, ``attrs`` is special; it is not covered
by ``CONTEXTS``.


TALES Exists expressions
========================

Syntax
++++++

Exists expression syntax::

  exists_expressions ::= 'exists:' path_expression

Description
+++++++++++

Exists expressions test for the existence of paths. An exists expression
returns true when the path expressions following it expression returns a value.
It is false when the path expression cannot locate an object.

Examples
++++++++

Testing for the existence of a form variable::

  <p tal:condition="not:exists:request/form/number">
    Please enter a number between 0 and 5
  </p>

Note that in this case you can't use the expression, ``not:request/form/number``,
since that expression will be true if the ``number`` variable exists and is zero.

TALES Nocall expressions
========================

Syntax
++++++

Nocall expression syntax::

  nocall_expression ::= 'nocall:' path_expression

Description
+++++++++++

Nocall expressions avoid rendering the results of a path expression.

An ordinary path expression tries to render the object that it fetches. This
means that if the object is a function, Script, Method, or some other kind of
executable thing, then expression will evaluate to the result of calling the
object. This is usually what you want, but not always. For example, if you want
to put a DTML Document into a variable so that you can refer to its properties,
you can't use a normal path expression because it will render the Document into
a string.

Examples
++++++++

Using nocall to get the properties of a document::

  <span tal:define="doc nocall:context/aDoc"
        tal:content="string:${doc/getId}: ${doc/title}">
    Id: Title
  </span>

Using nocall expressions on a functions::

  <p tal:define="join nocall:modules/string/join">

This example defines a variable:: ``join`` which is bound to the ``string.join``
function.

TALES Not expressions
=====================

Syntax
++++++

Not expression syntax::

  not_expression ::= 'not:' expression

Description
+++++++++++

Not expression evaluates the expression string (recursively) as a full
expression, and returns the boolean negation of its value. If the expression
supplied does not evaluate to a boolean value, *not* will issue a warning and
*coerce* the expression's value into a boolean type based on the following
rules:

1. the number 0 is *false*

2. positive and negative numbers are *true*

3. an empty string or other sequence is *false*

4. a non-empty string or other sequence is *true*

5. a #. *non-value*#. (e.g. void, None, Nil, NULL, etc) is *false*

6. all other values are implementation-dependent.

If no expression string is supplied, an error should be generated.

Zope considers all objects not specifically listed above as *false* to be
*true*.

Examples
++++++++

Testing a sequence::

  <p tal:condition="not:context/objectIds">
    There are no contained objects.
  </p>

TALES Path expressions
======================

Syntax
++++++

Path expression syntax::

  PathExpr    ::= Path [ '|' Expression ]
  Path        ::= variable [ '/' PathSegment ]*
  variable    ::= Name
  PathSegment ::= ( '?' variable ) | PathChar+
  PathChar    ::= AlphaNumeric | ' ' | '_' | '-' | '.' | ',' | '~'

Description
+++++++++++

A path expression consists of a *path* optionally followed by a vertical bar
(``|``) and alternate expression. A path consists of one or more non-empty strings
separated by slashes. The first string must be a variable name (a built-in
variable or a user defined variable), and the remaining strings, the *path
segments*, may contain letters, digits, spaces, and the punctuation characters
underscore, dash, period, comma, and tilde.

A limited amount of indirection is possible by using a variable name prefixed
with ``?`` as a path segment. The variable must contain a string, which replaces
that segment before the path is traversed.

For example::

  request/cookies/oatmeal
  nothing
  context/some-file 2009_02.html.tar.gz/foo
  root/to/branch | default
  request/name | string:Anonymous Coward
  context/?tname/macros/?mname

When a path expression is evaluated, Zope attempts to traverse the path, from
left to right, until it succeeds or runs out of paths segments. To traverse a
path, it first fetches the object stored in the variable. For each path
segment, it traverses from the current object to the sub-object named by the
path segment. Sub-objects are located according to standard Zope traversal rules
(via getattr, getitem, or traversal hooks).

Once a path has been successfully traversed, the resulting object is the value
of the expression. If it is a callable object, such as a method or template, it
is called.

If a traversal step fails, and no alternate expression has been specified, an
error results. Otherwise, the alternate expression is evaluated.

The alternate expression can be any TALES expression. For example::

  request/name | string:Anonymous Coward

is a valid path expression. This is useful chiefly for providing default
values, such as strings and numbers, which are not expressible as path
expressions. Since the alternate expression can be a path expression, it is
possible to "chain" path expressions, as in::

  first | second | third | nothing

If no path is given the result is *nothing*.

Since every path must start with a variable name, you need a set of starting
variables that you can use to find other objects and values. See the TALES
overview for a list of built-in variables. Variable names are looked up first
in locals, then in globals, then in the built-in list, so the built-in
variables act just like built-ins in Python: They are always available, but
they can be shadowed by a global or local variable declaration. You can always
access the built-in names explicitly by prefixing them with ``CONTEXTS``. (e.g.
``CONTEXTS/root``, ``CONTEXTS/nothing``, etc).

Examples
++++++++

Inserting a cookie variable or a property::

  <span tal:replace="request/cookies/pref | context/pref">
    preference
  </span>

Inserting the user name::

  <p tal:content="user/getUserName">
    User name
  </p>

TALES Python expressions
========================

Syntax
++++++

Python expression syntax::

  Any valid Python language expression

Description
+++++++++++

Python expressions evaluate Python code in a security-restricted environment.
Python expressions offer the same facilities as those available in Python-based
Scripts and DTML variable expressions.

Security Restrictions
~~~~~~~~~~~~~~~~~~~~~

Python expressions are subject to the same security restrictions as
Python-based scripts. These restrictions include:


access limits
  Python expressions are subject to Zope permission and role security
  restrictions. In addition, expressions cannot access objects whose names
  begin with underscore.

write limits
  Python expressions cannot change attributes of Zope objects.

Despite these limits malicious Python expressions can cause problems.

Built-in Functions
~~~~~~~~~~~~~~~~~~

Python expressions have the same built-ins as Python-based Scripts with a few
additions.

These standard Python built-ins are available:

- None

- abs

- apply

- bytes

- callable

- chr

- cmp

- complex

- delattr

- divmod

- filter

- float

- getattr

- hash

- hex

- int

- isinstance

- issubclass

- list

- len

- long

- map

- max

- min

- oct

- ord

- repr

- round

- setattr

- sorted

- str

- tuple

The ``range`` and ``pow`` functions are available and work the same way they do
in standard Python; however, they are limited to keep them from generating very
large numbers and sequences. This limitation helps to avoid accidental long
execution times.

These functions are available in Python expressions, but not in Python-based
scripts:

path(string)
  Evaluate a TALES path expression.

string(string)
  Evaluate a TALES string expression.

exists(string)
  Evaluates a TALES exists expression.

nocall(string)
  Evaluates a TALES nocall expression.

Python Modules
~~~~~~~~~~~~~~

A number of Python modules are available by default. You can make more modules
available. You can access modules either via path expressions (for example
``modules/string/join``) or in Python with the ``modules`` mapping object (for
example ``modules["string"].join``). Here are the default modules:

string
  The standard `Python string module
  <https://docs.python.org/library/string.html>`_ Note: most of
  the functions in the module are also available as methods on string objects.

random
  The standard `Python random module
  <https://docs.python.org/library/random.html>`_

math
  The standard `Python math module
  <https://docs.python.org/library/math.html>`_ .

sequence
  A module with a powerful sorting function. See sequence for more information.

Products.PythonScripts.standard
  Various HTML formatting functions available in DTML. See
  Products.PythonScripts.standard for more information.
  You need to install the ``Products.PythonScripts`` package before you can use
  this module.

ZTUtils
  Batch processing facilities similar to those offered by ``dtml-in``. See
  ZTUtils for more information.

AccessControl
  Security and access checking facilities. See AccessControl for more
  information.

Examples
++++++++

Using a module usage (pick a random choice from a list)::

  <span tal:replace="python:modules['random'].choice(
                         ['one', 'two', 'three', 'four', 'five'])">
    a random number between one and five
  </span>

String processing (capitalize the user name)::

  <p tal:content="python:user.getUserName().capitalize()">
    User Name
  </p>

Basic math (convert an image size to megabytes)::

  <p tal:content="python:image.getSize() / 1048576.0">
    12.2323
  </p>

String formatting (format a float to two decimal places)::

  <p tal:content="python:'%0.2f' % size">
    13.56
  </p>

TALES String expressions
========================

Syntax
++++++

String expression syntax::

  string_expression ::= ( plain_string | [ varsub ] )*
  varsub            ::= ( '$' Path ) | ( '${' Path '}' )
  plain_string      ::= ( '$$' | non_dollar )*
  non_dollar        ::= any character except '$'

Description
+++++++++++

String expressions interpret the expression string as text. If no expression
string is supplied the resulting string is *empty*. The string can contain
variable substitutions of the form ``$name`` or ``${path}``, where ``name`` is a
variable name, and ``path`` is a path expression. The escaped string value of the
path expression is inserted into the string. To prevent a ``$`` from being
interpreted this way, it must be escaped as ``$$``.

Examples
++++++++

Basic string formatting::

  <span tal:replace="string:$this and $that">
    Spam and Eggs
  </span>

Using paths::

  <p tal:content="string:total: ${request/form/total}">
    total: 12
  </p>

Including a dollar sign::

  <p tal:content="string:cost: $$$cost">
    cost: $42.00
  </p>

METAL Overview
==============

The *Macro Expansion Template Attribute Language* (METAL) standard is a
facility for HTML/XML macro preprocessing. It can be used in conjunction with
or independently of TAL and TALES.

Macros provide a way to define a chunk of presentation in one template, and
share it in others, so that changes to the macro are immediately reflected in
all of the places that share it. Additionally, macros are always fully
expanded, even in a template's source text, so that the template appears very
similar to its final rendering

METAL Namespace
+++++++++++++++

The METAL namespace URI and recommended alias are currently defined as::

  xmlns:metal="http://xml.zope.org/namespaces/metal"

Just like the TAL namespace URI, this URI is not attached to a web page; it's
just a unique identifier.

Zope does not require an XML namespace declaration when creating templates with
a content-type of ``text/html``. However, it does require an XML namespace
declaration for all other content-types.

METAL Statements
++++++++++++++++

METAL defines a number of statements:

- metal:define-macro - Define a macro.

- metal:use-macro - Use a macro.

- metal:define-slot - Define a macro customization point.

- metal:fill-slot - Customize a macro.

Although METAL does not define the syntax of expression non-terminals, leaving
that up to the implementation, a canonical expression syntax for use in METAL
arguments is described in TALES Specification.

define-macro: Define a macro
============================

Syntax
++++++

metal:define-macro syntax::

  argument ::= Name

Description
+++++++++++

The ``metal:define-macro`` statement defines a macro. The macro is named by the
statement expression, and is defined as the element and its sub-tree.

In Zope, a macro definition is available as a sub-object of a template's
``macros`` object. For example, to access a macro named ``header`` in a template
named ``master.html``, you could use the path expression::

  master.html/macros/header

Examples
++++++++

Simple macro definition::

  <p metal:define-macro="copyright">
    Copyright 2009, <em>Foobar</em> Inc.
  </p>


define-slot: Define a macro customization point
===============================================

Syntax
++++++

metal:define-slot syntax::

  argument ::= Name

Description
+++++++++++

The ``metal:define-slot`` statement defines a macro customization point or
*slot*. When a macro is used, its slots can be replaced, in order to customize
the macro. Slot definitions provide default content for the slot. You will get
the default slot contents if you decide not to customize the macro when using
it.

The ``metal:define-slot`` statement must be used inside a ``metal:define-macro``
statement.

Slot names must be unique within a macro.

Examples
++++++++

Simple macro with slot::

  <p metal:define-macro="hello">
    Hello <b metal:define-slot="name">World</b>
  </p>

This example defines a macro with one slot named ``name``. When you use this
macro you can customize the ``b`` element by filling the ``name`` slot.

fill-slot: Customize a macro
============================

Syntax
++++++

metal:fill-slot syntax::

  argument ::= Name

Description
+++++++++++

The ``metal:fill-slot`` statement customizes a macro by replacing a *slot* in the
macro with the statement element (and its content).

The ``metal:fill-slot`` statement must be used inside a ``metal:use-macro``
statement. Slot names must be unique within a macro.

If the named slot does not exist within the macro, the slot contents will be
silently dropped.

Examples
++++++++

Given this macro::

  <p metal:define-macro="hello">
    Hello <b metal:define-slot="name">World</b>
  </p>

You can fill the ``name`` slot like so::

  <p metal:use-macro="container/master.html/macros/hello">
    Hello <b metal:fill-slot="name">Kevin Bacon</b>
  </p>

use-macro: Use a macro
======================

Syntax
++++++

metal:use-macro syntax::

  argument ::= expression

Description
+++++++++++

The ``metal:use-macro`` statement replaces the statement element with a macro.
The statement expression describes a macro definition.

In Zope the expression will generally be a path expression referring to a macro
defined in another template. See ``metal:define-macro`` for more information.

The effect of expanding a macro is to graft a subtree from another document (or
from elsewhere in the current document) in place of the statement element,
replacing the existing sub-tree. Parts of the original subtree may remain,
grafted onto the new subtree, if the macro has *slots*. See
``metal:define-slot`` for more information. If the macro body uses any macros,
they are expanded first.

When a macro is expanded, its ``metal:define-macro`` attribute is replaced with
the ``metal:use-macro`` attribute from the statement element. This makes the root
of the expanded macro a valid ``use-macro`` statement element.

Examples
++++++++

Basic macro usage::

  <p metal:use-macro="container/other.html/macros/header">
    header macro from defined in other.html template
  </p>

This example refers to the ``header`` macro defined in the ``other.html``
template which is in the same folder as the current template. When the macro is
expanded, the ``p`` element and its contents will be replaced by the macro. Note:
there will still be a ``metal:use-macro`` attribute on the replacement element.

ZPT-specific Behaviors
======================

The behavior of Zope Page Templates is almost completely described by the TAL,
TALES, and METAL specifications. ZPTs do, however, have a few additional
features that are not described in the standards.

HTML Support Features
+++++++++++++++++++++

When the content-type of a Page Template is set to ``text/html``, Zope processes
the template somewhat differently than with any other content-type. As
mentioned under TAL Namespace, HTML documents are not required to declare
namespaces, and are provided with ``tal`` and ``metal`` namespaces by default.

HTML documents are parsed using a non-XML parser that is somewhat more
forgiving of malformed markup. In particular, elements that are often written
without closing tags, such as paragraphs and list items, are not treated as
errors when written that way, unless they are statement elements. This laxity
can cause a confusing error in at least one case; a ``<div>`` element is
block-level, and therefore technically not allowed to be nested in a ``<p>``
element, so it will cause the paragraph to be implicitly closed. The closing
``</p>`` tag will then cause a NestingError, since it is not matched up with the
opening tag. The solution is to use ``<span>`` instead.

Unclosed statement elements are always treated as errors, so as not to cause
subtle errors by trying to infer where the element ends. Elements which
normally do not have closing tags in HTML, such as image and input elements,
are not required to have a closing tag, or to use the XHTML ``<tag />`` form.

Certain boolean attributes, such as ``checked`` and ``selected``, are treated
differently by ``tal:attributes``. The value is treated as true or false (as
defined by ``tal:condition``). The attribute is set to ``attr="attr"`` in the true
case and omitted otherwise. If the value is ``default``, then it is treated as
true if the attribute already exists, and false if it does not. For example,
each of the following lines::

  <input type="checkbox" checked tal:attributes="checked default">
  <input type="checkbox" tal:attributes="checked string:yes">
  <input type="checkbox" tal:attributes="checked python:42">

will render as::

  <input type="checkbox" checked="checked">

while each of these::

  <input type="checkbox" tal:attributes="checked default">
  <input type="checkbox" tal:attributes="checked string:">
  <input type="checkbox" tal:attributes="checked nothing">

will render as::

  <input type="checkbox">

This works correctly in all browsers in which it has been tested.

