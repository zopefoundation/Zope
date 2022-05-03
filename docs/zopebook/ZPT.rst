Using Zope Page Templates
=========================

*Page Templates* are a web page generation tool.  They help programmers and
designers collaborate in producing dynamic web pages for Zope web
applications.  Designers can use them to maintain pages without having to
abandon their tools, while preserving the work required to embed those pages
in an application.

In this chapter, you'll learn the basic features of *Page Templates*,
including how you can use them in your website to create dynamic web pages
easily.  The next chapter walks you through a "hands on" example showing how
to build a Zope web application using scripts and *Page Templates*.  In the
chapter entitled `Advanced Page Templates <AdvZPT.html>`_, you'll learn about
advanced *Page Template* features.

The goal of *Page Templates* is to allow designers and programmers to work
together easily.  A designer can use a WYSIWYG HTML editor to create a
template, then a programmer can edit it to make it part of an application.
If required, the designer can load the template *back* into his editor and
make further changes to its structure and appearance.  By taking reasonable
steps to preserve the changes made by the programmer, the designer will not
disrupt the application.

*Page Templates* aim at this goal by adopting three principles:

1. Play nicely with editing tools.

2. What you see is very similar to what you get.

3. Keep code out of templates, except for structural logic.

A Page Template is like a model of the pages that it will generate.  In
particular, it is parseable by most HTML tools.

HTML Page Templates
-------------------

*Page Templates* can operate in two modes: *HTML Mode* and *XML Mode*.
Later in this chapter we will show you how to use the *XML Mode*, but in
most cases we want to use the *HTML Mode* which is also the default mode.
For the *HTML Mode* the *Content-Type* has to be set to ``text/html``.

HTML isn't XML-conform and can't be extended by a template language.  So
while rendered HTML *Page Templates* should return valid HTML, their
source code isn't valid HTML or XML.  But the *Template Attribute
Language* (*TAL*) does a good job in hiding itself in HTML tags, so most
HTML tools will be able to parse the source of HTML *Page Templates* and
just ignore the *TAL* attributes.

As you might already know, XHTML is a XML-conform reformulation of HTML
and widely used in our days.  Nevertheless, generating HTML and XHTML
with *Page Templates* works exactly the same way.  While the *HTML Mode*
doesn't enforce well-formed XML, it's absolutely fine to use this mode
also for XHTML.

How Page Templates Work
~~~~~~~~~~~~~~~~~~~~~~~

*Page Templates* use the *Template Attribute Language* (*TAL*).  *TAL*
consists of special tag attributes.  For example, a dynamic page
headline might look like this::

  <h1 tal:content="context/title">Sample Page Title</h1>

The ``tal:content`` attribute is a *TAL* statement.  Since it has an XML
namespace (the ``tal:`` part) most editing tools will not complain that
they don't understand it, and will not remove it.  It will not change
the structure or appearance of the template when loaded into a WYSIWYG
editor or a web browser.  The name *content* indicates that it will set
the text contained by the ``h1`` tag, and the value ``context/title`` is an
expression providing the text to insert into the tag.  Given the text
specified by ``context/title`` resolves to "Susan Jones Home Page", the
generated HTML snippet looks like this::

  <h1>Susan Jones Home Page</h1>

All *TAL* statements consist of tag attributes whose name starts with
``tal:`` and all *TAL* statements have values associated with them.  The
value of a *TAL* statement is shown inside quotes.  See Appendix C,
`Zope Page Templates Reference <AppendixC.html>`_, for more information
on *TAL*.

To the HTML designer using a WYSIWYG tool, the dynamic headline example
is perfectly parseable HTML, and shows up in their editor looking like a
headline should look like.  In other words, *Page Templates* play nicely
with editing tools.

This example also demonstrates the principle that "What you see is very
similar to what you get".  When you view the template in an editor, the
headline text will act as a placeholder for the dynamic headline text.
The template provides an example of how generated documents will look.

When this template is saved in Zope and viewed by a user, Zope turns the
dummy content into dynamic content, replacing "Sample Page Title" with
whatever ``context/title`` resolves to.  In this case, ``context/title``
resolves to the title of the object to which the template is applied.
This substitution is done dynamically, when the template is viewed.

There are template statements for replacing entire tags, their contents,
or just some of their attributes.  You can repeat a tag several times or
omit it entirely.  You can join parts of several templates together, and
specify simple error handling.  All of these capabilities are used to
generate document structures.  Despite these capabilities, you **can't**
create subroutines or classes, perform complex flow control, or easily
express complex algorithms using a *Page Template*.  For these tasks,
you should use Python-based Scripts or application components.

The *Page Template* language is deliberately not as powerful and
general-purpose as it could be.  It is meant to be used inside of a
framework (such as Zope) in which other objects handle business logic
and tasks unrelated to page layout.

For instance, template language would be useful for rendering an invoice
page, generating one row for each line item, and inserting the
description, quantity, price, and so on into the text for each row.  It
would not be used to create the invoice record in a database or to
interact with a credit card processing facility.

Creating a Page Template
~~~~~~~~~~~~~~~~~~~~~~~~

Use your web browser to log into the Zope Management Interface as a manager.
Create a *Folder* to work in named ``template_test`` in the root of your Zope.
Visit this folder and choose *Page Template* from Zope's add list. Type
``simple_page`` in the add form's *Id* field, then push the *Add and Edit*
button.

You should now see the main editing page for the new *Page Template*.
The title is blank and the default template text is in the editing area.

Now let's create a simple dynamic page.  Type the words ``a Simple Page``
in the *Title* field.  Then, edit the template text to look like this::

  <html>
    <body>
      <p>
        This is <b tal:content="template/title">the Title</b>.
      </p>
    </body>
  </html>

Now push the *Save Changes* button.  Zope should show a message
confirming that your changes have been saved.

If you get an error message, check to make sure you typed the example
correctly and save it again.

Click on the *Test* tab.  You should see a page with "This is **a Simple
Page**." at the top.  Notice that the title is bold.  This is because
the ``tal:content`` statement just replaces the content of the *bold* tag.

Back up, then click on the eye symbol on the right hand side above the source
code input field.  This will show you the *unrendered* source of the
template.  You should see, "This is **the Title**." The bold text acts
as a placeholder for the dynamic title text.  Back up again, so that you
are ready to edit the example further.

You can find two options on the *Edit* tab we will not touch for now:
The *Content-Type* field allows you to specify the content type of
your page.  Changing that value switches the *Page Template* into *XML
Mode*, discussed later in this chapter.  The *Expand macros when
editing* control is explained in the "Macros" section of this chapter.

*TALES* Expressions
~~~~~~~~~~~~~~~~~~~

The expression ``template/title`` in your simple Page Template is a *path
expression*.  This is the most common type of expression.  There are
several other types of expressions defined by the *TAL Expression
Syntax* (*TALES*) specification.  For more information on TALES see
Appendix C, `Zope Page Templates Reference`_.

Path Expressions
%%%%%%%%%%%%%%%%

The ``template/title`` *path expression* fetches the *title* attribute
of the template.  Here are some other common path expressions:

- ``context/objectValues``: A list of the sub-objects of the folder on
  which the template is called.

- ``request/URL``: The URL of the current web request.

- ``user/getUserName``: The authenticated user's login name.

From the last chapter you should already be familiar with the context
variable that is also available in *Python-based Scripts* and the
attribute ``objectValues`` that specifies an API method.  The other two
examples are just to show you the pattern.  You will learn more about
them later in the book.

To see what these examples return, just copy the following lines into
a *Page Template* and select the *Test* tab.  You'll notice that
``context/objectValues`` returns a list that needs further treatment to
be useful.  We'll come back to that later in this chapter::

  <p tal:content="context/objectValues"></p>
  <p tal:content="request/URL"></p>
  <p tal:content="user/getUserName"></p>

Every *path expression* starts either with a variable name or with
a (supported) builtin.  The available
variable names refer either to objects like *context*, *request* or
*user* that are bound to every *Page Template* by default or variables
defined within the *Page Template* using TAL.  Note that *here* is an
old alias of *context* and still used in many places.

The small set of built-in variables such as *request* and *user* is
described in the chapter entitled `Advanced Page Templates`_.
You will also learn how to define your own variables in that chapter.

If the variable itself returns the value you want, you are done.
Otherwise, you add a slash ('``/``) and the name of a sub-object or
attribute.  You may need to work your way through several
sub-objects to get to the value you're looking for.

Which builtins are supported as first element of a path
expression depends on the context. In an untrusted context,
only "safe builtins" (as specified by ``AccessControl.safe_builtins``)
are supported; in a trusted context, beside those all
Python builtins are supported in addition (and take precedence over
the former). Note that many builtins are callable. For those,
you will refer to them usually via the ``nocall`` variant of
a path expression.

Python Expressions
%%%%%%%%%%%%%%%%%%

A good rule of thumb is that if you need Python to express your logic,
you better factor out the code into a script.  But Zope is a good tool
for prototyping and sometimes it would be overkill to write a script
for one line of code.  And looking at existing products you will see
quite often 'Python expressions', so it's better to know them.

Recall the first example of this chapter::

  <h1 tal:content="context/title">Sample Page Title</h1>

Let's try to rewrite it using a *Python expression*::

  <h1 tal:content="python: context.title">Sample Page Title</h1>

While *path expressions* are the default, we need a prefix to indicate other
expression types. This expression with the prefix ``python:`` does (at least
here) the same as the *path expression* above. *Path expressions* try different
ways to access ``title``, so in general they are more flexible, but less
explicit.

There are some simple things you can't do with *path expressions*.
The most common are comparing values like in::

  "python: variable1 == variable2"

... or passing arguments to methods, e.g.::

  "python: context.objectValues(['Folder'])"

*TAL* Attributes
~~~~~~~~~~~~~~~~

*Page Templates* are example pages or snippets.  *TAL* statements define
how to convert them dynamically.  Depending on the used *TAL* attribute
they substitute example content or attributes by dynamic values, or
remove or repeat example elements depending on dynamic values.

Inserting Text
%%%%%%%%%%%%%%

  In your "simple_page" template, you used the ``tal:content`` statement
  on a *bold* tag.  When you tested it, Zope replaced the content of the
  HTML *bold* element with the title of the template.

  This is easy as long as we want to replace the complete content of an
  HTML element.  But what if we want to replace only some words within
  an element?

  In order to place dynamic text inside of other text, you typically use
  ``tal:replace`` on an additional ``span`` tag.  For example, add the
  following lines to your example::

    <p>The URL is
      <span tal:replace="request/URL">
        http://www.example.com</span>.</p>

  The ``span`` tag is structural, not visual, so this looks like "The URL
  is http://www.example.com." when you view the source in an editor or
  browser.  When you view the rendered version, however, it may look
  something like::

    The URL is http://localhost:8080/template_test/simple_page.

  If you look at the source code of the rendered version, the *span*
  tags are removed.

  To see the difference between ``tal:replace`` and ``tal:content``, create
  a page template and include the following in the body::

    <b tal:content="template/title"></b>
    <b tal:content="request/URL"></b>
    <b tal:content="user/getUserName"></b>
    <b tal:replace="template/title"></b>
    <b tal:replace="request/URL"></b>
    <b tal:replace="user/getUserName"></b>

  There are two other ways to add elements that are only needed for
  *TAL* attributes and that are removed again in the rendered version::

    <p>The URL is
      <span tal:content="request/URL" tal:omit-tag="">
        http://www.example.com</span>.</p>

  ... which is more useful in other situations and will be discussed
  there and::

    <p>The URL is
      <tal:span tal:content="request/URL">
        http://www.example.com</tal:span>.</p>

  While you can get really far by using HTML elements and ``tal:replace``
  or ``tal:omit-tag``, some people prefer to use *TAL* elements if the
  elements are only used to add *TAL* attributes.  *TAL* is an attribute
  language and doesn't define any elements like ``tal:span``, but it uses
  a complete XML namespace and allows to use any element name you like.
  They are silently removed while the *Page Template* is rendered.

  This is useful for using speaking names like ``tal:loop``, ``tal:case`` or
  ``tal:span`` and to insert additional elements where HTML doesn't allow
  elements like ``span`` or ``div``.  And if her browser or editor also
  ignores these tags, the designer will have less trouble with *TAL*
  elements than with additional HTML elements.

Repeating Structures
%%%%%%%%%%%%%%%%%%%%

Let's start with a simple three-liner::

  <p tal:repeat="number python: range(4)" tal:content="number">
    999
  </p>

``number`` is our *repeat variable* and ``range(4)`` is a *Python
expression* that returns the list ``[0, 1, 2, 3]``.  If this code is
rendered, the ``repeat`` statement repeats the *paragraph* element for
each value of the sequence, replacing the variable ``number`` by the
current sequence value.  So the rendered page will not show the
example number ``999``, but 4 *paragraph* elements containing the
numbers of our list.

In most cases we want to iterate over more complex sequences.  Our
next example shows how to use a sequence of (references to) objects.
The "simple_page" template could be improved by adding an item list,
in the form of a list of the objects that are in the same *Folder* as
the template.  You will make a table that has a row for each object,
and columns for the id, meta-type and title.  Add these lines to the
bottom of your example template::

  <table border="1" width="100%">
    <tr>
      <th>Id</th>
      <th>Meta-Type</th>
      <th>Title</th>
    </tr>
    <tr tal:repeat="item context/objectValues">
      <td tal:content="item/getId">Id</td>
      <td tal:content="item/meta_type">Meta-Type</td>
      <td tal:content="item/title">Title</td>
    </tr>
  </table>

The ``tal:repeat`` statement on the table row means "repeat this row for
each item in my context's list of object values".  The *repeat*
statement puts the objects from the list into the *item* variable one
at a time (this is called the *repeat variable*), and makes a copy of
the row using that variable.  The value of ``item/getId`` in each row is
the Id of the object for that row, and likewise with ``item/meta_type``
and ``item/title``.

You can use any name you like for the repeat variable (``item`` is only
an example), as long as it starts with a letter and contains only
letters, numbers, and underscores (``_``).  The repeat variable is only
defined in the repeat tag.  If you try to use it above or below the
*tr* tag you will get an error.

You can also use the repeat variable name to get information about the
current repetition.  See `Advanced Page Templates`_.

Now view the page and notice how it lists all the objects in the same
folder as the template.  Try adding or deleting objects from the
folder and notice how the page reflects these changes.

Conditional Elements
%%%%%%%%%%%%%%%%%%%%

Using Page Templates you can dynamically query your environment and
selectively insert text depending on conditions.  For example, you
could display special information in response to a cookie::

  <p tal:condition="request/cookies/verbose | nothing">
    Here's the extra information you requested.
  </p>

This paragraph will be included in the output only if there is a
``verbose`` cookie set.  The expression, ``request/cookies/verbose |
nothing`` is true only when there is a cookie named ``verbose`` set.
You'll learn more about this kind of expression in the chapter
entitled `Advanced Page Templates`_.

Using the ``tal:condition`` statement you can check all kinds of
conditions.  A ``tal:condition`` statement leaves the tag and its
contents in place if its expression has a true value, but removes them
if the value is false.  Zope considers the number zero, a  blank
string, an empty list, and the built-in variable ``nothing`` to be false
values.  Nearly every other value is true, including non-zero numbers,
and strings with anything in them (even spaces!).

Another common use of conditions is to test a sequence to see if it is
empty before looping over it.  For example in the last section you saw
how to draw a table by iterating over a collection of objects.  Here's
how to add a check to the page so that if the list of objects is empty
no table is drawn.

To allow you to see the effect, we first have to modify that example
a bit, showing only *Folder* objects in the context folder.  Because
we can't specify parameters using *path expressions* like
``context/objectValues``, we first convert it into the *Python
expression* ``context.objectValues()`` and then add the argument that
tells the ``objectValues`` method to return only sub-folders::

  <tr tal:repeat="item python: context.objectValues(['Folder'])">

If you did not add any sub-folders to the *template_test* folder so
far, you will notice that using the *Test* tab the table header is
still shown even if we have no table body.  To avoid this we add a
``tal:condition`` statement in the table tag.  The complete table now
looks like this::

  <table tal:condition="python: context.objectValues(['Folder'])"
         border="1" width="100%">
    <tr>
      <th>Id</th>
      <th>Meta-Type</th>
      <th>Title</th>
    </tr>
    <tr tal:repeat="item python: context.objectValues(['Folder'])">
      <td tal:content="item/getId">Id</td>
      <td tal:content="item/meta_type">Meta-Type</td>
      <td tal:content="item/title">Title</td>
    </tr>
  </table>

If the list of sub-folders is an empty list, the condition is false
and the entire table is omitted.  You can verify this by using the
*Test* tab again.

Go and add three Folders named ``1``, ``2``, and ``3`` to the
*template_test* folder in which your *simple_page* template lives.
Revisit the *simple_page* template and view the rendered output via
the *Test* tab.  You will see a table that looks much like the below::

  Id          Meta-Type          Title
  1           Folder
  2           Folder
  3           Folder


XML Page Templates
------------------

Creating XML with *Page Templates* is almost exactly like creating HTML.
You switch to *XML Mode* by setting the *content-type* field to
``text/xml`` or whatever the content-type for your XML should be.

In *XML Mode* no "loose" markup is allowed.  Zope assumes that your
template is well-formed XML.  Zope also requires an explicit TAL and METAL
XML namespace declarations in order to emit XML.  For example, if you wish
to emit XHTML, you might put your namespace declarations on the ``html``
tag::

  <html xmlns:tal="http://xml.zope.org/namespaces/tal"
    xmlns:metal="http://xml.zope.org/namespaces/metal">

To browse the source of an XML template you go to ``source.xml`` rather than
``source.html``.

Debugging and Testing

Zope helps you find and correct problems in your *Page Templates*.  Zope
notices problems at two different times: when you're editing a *Page
Template*, and when you're viewing a *Page Template*.  Zope catches
different types of problems when you're editing and than when you're
viewing a *Page Template*.

You may have already seen the troubleshooting comments that Zope inserts
into your Page Templates when it runs into problems.  These comments tell
you about problems that Zope finds while you're editing your templates.
The sorts of problems that Zope finds when you're editing are mostly
errors in your *TAL* statements.  For example::

    <!-- Page Template Diagnostics
     Compilation failed
     chameleon.exc.CompilationError: Bad attribute for namespace 'http://xml.zope.org/namespaces/tal'
    
     - String:     "contents"
     - Filename:   /template_test/simple_page
     - Location:   (line 4: col 21)
     - Source:     This is <b tal:contents="template/title">the Title</b>.
                                  ^^^^^^^^
    -->

This diagnostic message lets you know that you mistakenly used
``tal:contents`` rather than ``tal:content`` on line 4 of your template.
Other diagnostic messages will tell you about problems with your template
expressions and macros.

When you're using the Zope management interface to edit *Page Templates*
it's easy to spot these diagnostic messages, because they are shown in the
"Errors" header of the management interface page when you save the *Page
Template*.

If you don't notice the diagnostic message and try to render a template
with problems you'll see a message like this::

  Error Type: PTRuntimeError
  Error Value: Page Template hello.html has errors.

That's your signal to reload the template and check out the diagnostic
message.

In addition to diagnostic messages when editing, you'll occasionally get
regular Zope errors when viewing a Page Template.  These problems are
usually due to problems in your template expressions.  For example, you
might get an error if an expression can't locate a variable::

  Error Type: KeyError
  Error Value: 'unicorn'

This error message tells you that it cannot find the *unicorn* variable.
To help you figure out what went wrong, Zope includes information about
the environment in the traceback.  This information will be available in
your *error_log* (in your Zope root folder).  The traceback will include
information about the place where the error occurred and the environment::

  URL: /sandbox/demo
  Line 1, Column 14
  Expression: standard:'context/unicorn'
  Names:
    {'container': <Folder instance at 019AC4D0>,
     'context': <Application instance at 01736F78>,
     'default': <Products.PageTemplates.TALES.Default instance at 0x012F9D00>,
     ...
     'root': <Application instance at 01736F78>,
     'template': <ZopePageTemplate at /sandbox/demo>,
     'traverse_subpath': [],
     'user': admin}

This information is a bit cryptic, but with a little detective work it can
help you figure out what went wrong.  In this case, it tells us that the
``context`` variable is an "Application instance".  This means that it is
the top-level Zope folder (notice how ``root`` variable is the same
"Application instance").  Perhaps the problem is that you wanted to apply
the template to a folder that had a *unicorn* property, but the root on
which you called the template hasn't such a property.

Macros
------

So far, you've seen how *Page Templates* can be used to add dynamic
behavior to individual web pages.  Another feature of page templates is
the ability to reuse look and feel elements across many pages.

For example, with *Page Templates*, you can have a site that has a
standard look and feel.  No matter what the "content" of a page, it will
have a standard header, side-bar, footer, and/or other page elements.
This is a very common requirement for websites.

You can reuse presentation elements across pages with *macros*.  Macros
define a section of a page that can be reused in other pages.  A macro can
be an entire page, or just a chunk of a page such as a header or footer.
After you define one or more macros in one *Page Template*, you can use
them in other *Page Templates*.

Using Macros
~~~~~~~~~~~~

You can define macros with tag attributes similar to *TAL* statements.
Macro tag attributes are called *Macro Expansion Tag Attribute Language*
(*METAL*) statements.  Here's an example macro definition::

  <p metal:define-macro="copyright">
    Copyright 2009, <em>Foo, Bar, and Associates</em> Inc.
  </p>

This ``metal:define-macro`` statement defines a macro named "copyright".
The macro consists of the ``p`` element (including all contained elements,
ending with the closing ``p`` tag).

Macros defined in a Page Template are stored in the template's *macros*
attribute.  You can use macros from other *Page Templates* by referring
to them through the *macros* attribute of the *Page Template* in which
they are defined.  For example, suppose the *copyright* macro is in a
*Page Template* called "master_page".  Here's how to use the *copyright*
macro from another *Page Template*::

  <hr />
  <b metal:use-macro="container/master_page/macros/copyright">
    Macro goes here
  </b>

In this *Page Template*, the ``b`` element will be completely replaced by
the macro when Zope renders the page::

  <hr />
  <p>
    Copyright 2009, <em>Foo, Bar, and Associates</em> Inc.
  </p>

If you change the macro (for example, if the copyright holder changes)
then all *Page Templates* that use the macro will automatically reflect
the change.

Notice how the macro is identified by a *path expression* using the
``metal:use-macro`` statement.  The ``metal:use-macro`` statement replaces
the statement element with the named macro.

Macro Details
~~~~~~~~~~~~~

The ``metal:define-macro`` and ``metal:use-macro`` statements are pretty
simple.  However there are a few subtleties to using them which are
worth mentioning.

A macro's name must be unique within the Page Template in which it is
defined.  You can define more than one macro in a template, but they all
need to have different names.

Normally you'll refer to a macro in a ``metal:use-macro`` statement with a
path expression.  However, you can use any expression type you wish so
long as it returns a macro.  For example::

  <p metal:use-macro="python:context.getMacro()">
    Replaced with a dynamically determined macro,
    which is located by the getMacro script.
  </p>

In this case the python expression returns a macro defined dynamically by
the 'getMacro' script.  Using *Python expressions* to locate macros lets
you dynamically vary which macro your template uses.  An example
of the body of a ``getMacro`` Script (Python) is as follows::

  return container.ptMacros.macros['amacroname']

You can use the '``default`` variable with the 'metal:use-macro'
statement::

  <p metal:use-macro="default">
    This content remains - no macro is used
  </p>

The result is the same as using *default* with ``tal:content`` and
``tal:replace``.  The "default" content in the tag doesn't change when it
is rendered.  This can be handy if you need to conditionally use a macro
or fall back on the default content if it doesn't exist.

If you try to use the ``nothing`` variable with ``metal:use-macro`` you will
get an error, since ``nothing`` is not a macro.  If you want to use
``nothing`` to conditionally include a macro, you should instead enclose
the ``metal:use-macro`` statement with a ``tal:condition`` statement.

Zope handles macros first when rendering your templates.  Then Zope
evaluates TAL expressions.  For example, consider this macro::

  <p metal:define-macro="title"
     tal:content="template/title">
    template's title
  </p>

When you use this macro it will insert the title of the template in
which the macro is used, *not* the title of the template in which the
macro is defined.  In other words, when you use a macro, it's like
copying the text of a macro into your template and then rendering your
template.

If you check the *Expand macros when editing* option on the *Page
Template* *Edit* view, then any macros that you use will be expanded in
your template's source.

Using Slots
~~~~~~~~~~~

Macros are much more useful if you can override parts of them when you
use them.  You can do this by defining *slots* in the macro that you can
fill in when you use the template.  For example, consider a side bar
macro::

  <div metal:define-macro="sidebar">
    Links
    <ul>
      <li><a href="/">Home</a></li>
      <li><a href="/products">Products</a></li>
      <li><a href="/support">Support</a></li>
      <li><a href="/contact">Contact Us</a></li>
    </ul>
  </div>

This macro is fine, but suppose you'd like to include some additional
information in the sidebar on some pages.  One way to accomplish this is
with slots::

  <div metal:define-macro="sidebar">
    Links
    <ul>
      <li><a href="/">Home</a></li>
      <li><a href="/products">Products</a></li>
      <li><a href="/support">Support</a></li>
      <li><a href="/contact">Contact Us</a></li>
    </ul>
    <span metal:define-slot="additional_info"></span>
  </div>

When you use this macro you can choose to fill the slot like so::

  <p metal:use-macro="container/master.html/macros/sidebar">
    <b metal:fill-slot="additional_info">
      Make sure to check out our <a href="/specials">specials</a>.
    </b>
  </p>

When you render this template the side bar will include the extra
information that you provided in the slot::

  <div>
    Links
    <ul>
      <li><a href="/">Home</a></li>
      <li><a href="/products">Products</a></li>
      <li><a href="/support">Support</a></li>
      <li><a href="/contact">Contact Us</a></li>
    </ul>
    <b>
      Make sure to check out our <a href="/specials">specials</a>.
    </b>
  </div>

Notice how the ``span`` element that defines the slot is replaced with the
``b`` element that fills the slot.

Customizing Default Presentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A common use of slot is to provide default presentation which you can
customize.  In the slot example in the last section, the slot definition
was just an empty ``span`` element.  However, you can provide default
presentation in a slot definition.  For example, consider this revised
sidebar macro::

  <div metal:define-macro="sidebar">
    <div metal:define-slot="links">
    Links
    <ul>
      <li><a href="/">Home</a></li>
      <li><a href="/products">Products</a></li>
      <li><a href="/support">Support</a></li>
      <li><a href="/contact">Contact Us</a></li>
    </ul>
    </div>
    <span metal:define-slot="additional_info"></span>
  </div>

Now the sidebar is fully customizable.  You can fill the 'links' slot to
redefine the sidebar links.  However, if you choose not to fill the
'links' slot then you'll get the default links, which appear inside the
slot.

You can even take this technique further by defining slots inside of
slots.  This allows you to override default presentation with a fine
degree of precision.  Here's a sidebar macro that defines slots within
slots::

  <div metal:define-macro="sidebar">
    <div metal:define-slot="links">
    Links
    <ul>
      <li><a href="/">Home</a></li>
      <li><a href="/products">Products</a></li>
      <li><a href="/support">Support</a></li>
      <li><a href="/contact">Contact Us</a></li>
      <span metal:define-slot="additional_links"></span>
    </ul>
    </div>
    <span metal:define-slot="additional_info"></span>
  </div>

If you wish to customize the sidebar links you can either fill the
``links`` slot to completely override the links, or you can fill the
``additional_links`` slot to insert some extra links after the default
links.  You can nest slots as deeply as you wish.

Combining METAL and TAL
~~~~~~~~~~~~~~~~~~~~~~~

You can use both *METAL* and *TAL* statements on the same elements.  For
example::

  <ul metal:define-macro="links"
      tal:repeat="link context/getLinks">
    <li>
      <a href="link url"
         tal:attributes="href link/url"
         tal:content="link/name">link name</a>
    </li>
  </ul>

In this case, ``getLinks`` is an (imaginary) Script that assembles a list
of link objects, possibly using a Catalog query.

Since METAL statements are evaluated before *TAL* statements, there are
no conflicts.  This example is also interesting since it customizes a
macro without using slots.  The macro calls the ``getLinks`` Script to
determine the links.  You can thus customize your site's links by
redefining the ``getLinks`` Script at different locations within your
site.

It's not always easy to figure out the best way to customize look and
feel in different parts of your site.  In general you should use slots
to override presentation elements, and you should use Scripts to provide
content dynamically.  In the case of the links example, it's arguable
whether links are content or presentation.  Scripts probably provide a
more flexible solution, especially if your site includes link content
objects.

Whole Page Macros
~~~~~~~~~~~~~~~~~

Rather than using macros for chunks of presentation shared between
pages, you can use macros to define entire pages.  Slots make this
possible.  Here's an example macro that defines an entire page::

  <html metal:define-macro="page">
    <head>
      <title tal:content="context/title">The title</title>
    </head>

    <body>
      <h1 metal:define-slot="headline"
          tal:content="context/title">title</h1>

      <p metal:define-slot="body">
        This is the body.
      </p>

      <span metal:define-slot="footer">
        <p>Copyright 2009 Fluffy Enterprises</p>
      </span>

    </body>
  </html>

This macro defines a page with three slots, ``headline``, ``body``, and
``footer``.  Notice how the ``headline`` slot includes a *TAL* statement to
dynamically determine the headline content.

You can then use this macro in templates for different types of content,
or different parts of your site.  For example here's how a template for
news items might use this macro::

  <html metal:use-macro="container/master.html/macros/page">

    <h1 metal:fill-slot="headline">
      Press Release:
      <span tal:replace="context/getHeadline">Headline</span>
    </h1>

    <p metal:fill-slot="body"
       tal:content="context/getBody">
      News item body goes here
    </p>

  </html>

This template redefines the ``headline`` slot to include the words "Press
Release" and call the ``getHeadline`` method on the current object.  It
also redefines the ``body`` slot to call the ``getBody`` method on the
current object.

The powerful thing about this approach is that you can now change the
``page`` macro and the press release template will be automatically
updated.  For example you could put the body of the page in a table and
add a sidebar on the left and the press release template would
automatically use these new presentation elements.

Using Templates with Content
----------------------------

In general Zope supports content, presentation and logic components.
*Page Templates* are presentation components and they can be used to
display content components.

Zope ships with several content components such as Files, and Images.
You can use Files for textual content since you can edit the contents of Files
if the file is less than 64K and contains text. However, the File object is
fairly basic and may not provide all of the features or metadata that you need.
