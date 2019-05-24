=========================
Request parameter support
=========================

Introduction
============

Zope responds to requests, specified via an url, request headers
and (optionally) a request body. An url consists of
various parts, among them a *path* and a *query*
(for details see `RFC 2396 <https://www.ietf.org/rfc/rfc2396.txt>`_).
Zope uses *path* to locate an object, method or view responsible to
produce the response (this process is called *traversal*)
and *query* (if present) as a specification for
request parameters. Additionally, request parameters can come from
an (optional) request body.

Zope preprocesses the incoming request information and makes
the result available in the so called *request* object.
This way, the response generation can access all relevant request information
in an easy natural (pythonic) way.
We say that preprocessing transforms the request *parameters*
into request (or form) *variables*.
Those are made available via the request object's ``form`` attribute
(a ``dict``)
or directly via the request object itself (if not hidden by other
request information).

The request parameters coming from the "query" have the form
*name*\ ``=``\ *value* and are separated by ``&``;
request parameters from a request body can have different forms
and can be separated in different ways (dependent on the
request's ``Content-Type``), but they, too, have a *name* and a *value*.

All request parameter names and values are strings.
A parameter value, however, often designates a value of a specific type,
e.g. an integer or a datetime. The response generating code often can
be significantly simplified when it does not need to make the
type conversion itself. In addition, in some cases, the request parameters
are not independent from one another, but some of them are related; in those
cases, it can help, when the related parameters
are aggregated into a single object. Zope supports both cases but it needs
directives to guide the process. It uses *name* suffixes of the form
``:``\ *directive* to specify such directives. For example,
the parameter ``i:int=1`` tells Zope to convert the value ``'1'`` to an
integer and use it as value for request variable ``i``; the parameter sequence
``x.name:record=Peter&x.age:int:record=10`` tells Zope to contruct
a record ``x`` with attributes ``name`` and ``age`` and respective values ``'Peter'`` and ``10``.

The remaining parts of this document describe the available kinds
of directives and the overall processing model.


Request parameter directive kinds
=================================

Zope supports different kinds of request parameter directives.
This sections describes them in detail.


Converter
---------

A converter directive converts the parameter value (a string) to a converter
specific type in a coverter specific way. The available converters are given
by ``ZPublisher.Converters.type_converters``.

Simple type converters are ``int``, ``float``, ``boolean``, ...
each converting to the respective type.

Some converters employ special logic for the conversion.
For example, both ``tokens`` as well as ``lines`` convert to
a list of strings but ``tokens`` splits the input at whitespace, ``lines``
at newlines.

The converter ``required`` contains only logic: it checks that
the value is not empty.

Different Zope versions can support different converters.


Encoding
--------

An encoding directive tells the converting process the encoding
of the parameter value. Typical encodings are "utf8", "latin1" ...

An encoding directive is ignored, if the parameter does not
have a converter directive as well. In some sense, the encoding
directive informs the converter about the value's encoding.
If there is no encoding directive, the converter uses the
default encoding (specified via the configuration option
``zpublisher-default-encoding``).

In principle, Zope supports any encoding known by the ``codecs``
module. However, the converter may impose restrictions.


Aggregator
----------

An aggregator directive tells Zope how to process parameters with
a similar name.

Zope supports the following aggregators:

list
  collect all values with this name into a list.

  If there are more than a single parameter with the same name,
  then they are by default collected into a list.
  The ``list`` aggregator is mainly used to ensure that
  the parameter leads to a list value even in the case that
  there is only one of them.

tuple
  collect all values with this name into a tuple.

default
  use the value of this parameter as a default value; it
  can be overridden by a parameter of the same name without
  the ``default`` directive.

record
  this directive assumes that the parameter name starts with
  *var*\ ``.``\ *attr*.

  It tells Zope to create a request variable *var*
  with as value a 
  record (i.e. a ``ZPublisher.HTTPRequest.record`` instance) and
  set its attribute *attr* to the parameter value.
  If such a request variable already exists,
  then only its attribute *attr* is updated.

records
  this directive is similar to ``record``. However, *var*
  gets as value not a single record but a list of records.

  Zope starts a new record (and appends it to the list)
  when the current request parameter would override an attribute 
  in the last record of the list constructed so far (or this list
  is empty).

ignore_empty
  this directive causes Zope to ignore the parameter if its
  value is empty.


Method
------

Usually, a request parameter is transformed into a request variable
(and made available via the ``form`` attribute of the request object). The
method directives tell Zope to instead extend the path used for traversal.

The resulting path
is the original path from the url extended by a value derived from
the request parameter. If the parameter name starts with the directive,
then the parameter value is used to extend the path; otherwise, the
name prefix up to the method directive is used.

Zope supports the following method directives:
``method`` (with synonym ``action``) and ``default_method`` (with
synonym ``default_action``). A path extension specified by a
``method_default`` directive is overridden by a ``method`` directive.


Processing model
================

Zope processes the request parameters in
`ZPublisher.HTTPRequest.HTTPRequest.processInputs`.

The processing involves various steps and
peculiar logic which may lead to surprises.
Therefore, this section describes the processing model in some detail.

In a preliminary step the request parameters are collected
from the potential sources (i.e. the "query" and (potentially) the
request body) and normalized. The result is a sequence of
name, value pairs, each describing a single request parameter.

Zope then sets up some variables:

form
  as target for the collected form variables
  
defaults
  as target for the collected form variable defaults

tuple_items
  to remember which form variable should be tuples
  
method
  as target for the path extension from method directives.

It then loops over the request parameter sequence.


For each request parameter, the processing consists of the following steps:

1. Some variables are set up:

   isFileUpload
     does the parameter represents an uploaded file?

   converter_type
     the most recently seen converter from a converter directive

   character_encoding
     the most recently seen encoding from an encoding directive

   flags
     indicate by flag bits which processing types are requested via directives

     Processing types are "ignore", "aggregate as sequence",
     "aggregate as record", "aggregate as records", "use as default",
     "convert" (using ``converter_type`` and ``character_encoding``)

2. It is checked whether the parameter value corresponds to an uploaded file.
   In this case, it is wrapped into a ``FileUpload`` and ``isFileUpload``
   is updated


3. All directives in the paramter name are examined from right to left
   and the variables set up in step 1 are updated accordingly.
   A ``:tuple`` directive updates in addtion ``tuple_items``.
   A method directive updates instead ``method``.

4. The actions remembered in ``flags`` by step 3 are executed.

   If ``flags`` indicates the use as default, then this operates
   on ``defaults``, otherwise on ``form``.

After all request parameters have been processed,
request variables from ``defaults`` are put into ``form`` if this
does not yet contain such a variable.
If a method directive has been processed, then the traversal
path is extended accordingly.

As a security measure, mainly for DTML use, request variables
are not only made available in the request attribute ``form``;
a (somewhat) securized version of them is made available in
the attribute ``taintedform``. In the *tainted* request variable
variant, strings potentially containing HTML fragments use
``TaintedString`` as data type rather than the normal ``str``.
DTML will automatically (HTML) quote those values which gives some
protection against cross site scripting attacks via HTML injection.
With the more modern page templates, all values (not only tainted ones)
are by default (HTML) quoted: they typically do not use the tainted
form of the request variables.


Known Bugs/Caveats
==================

1. There is almost no error handling:

   - unrecognized directives are silently ignored

   - if a request paramater contains several converter directives, the 
     left most wins

   - if a request paramter contains several encoding directives, the
     left most wins

   - if a request parameter contains an encoding but no converter
     directive, the encoding directive is silently ignored

   - some directive combinations do not make sense (e.g. ``:record:records``);
     for them, some of the directives are silently ignored

2. Usually, the order of aggregator directives in a request parameter does
   not matter. However, this is not the case for the ``:tuple`` directive.
   To really produce a tuple request variable, it must be the left most
   directive; otherwise, it is equivalent to ``:list``.

   In addition, ``:tuple`` is always equivalent to ``:list`` for
   request variables aggregated as record or sequence of records.

3. The main use case for the ``:default`` directive it to provide a
   default value for form controls (e.g. checkboxes) for which the browser may
   or may not pass on a value when the form is submitted.
   Unfortunately, this works only at the top level;
   it does not work for subcomponents, e.g. an attribute of a "record".
   As a consequence, if a request parameter combines ``:default`` with
   another aggregator directive, the result will likely be surprising.

4. The request preprocessing happens at a very early stage. Especially,
   the traversal has not yet taken place. As a consequence,
   important configuration for application specific error handling
   may not yet have taken effect; exceptions raised during this stage
   are reported and tracked only via "root level" error handling.
   For form processing, it is therefore typically better to
   use a form subframework (such as ``z3c.form`` or ``zope.formlib``)
   rather than the elementary features described in this document.
