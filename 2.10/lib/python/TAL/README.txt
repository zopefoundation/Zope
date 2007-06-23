TAL - Template Attribute Language
---------------------------------

This is an implementation of TAL, the Zope Template Attribute
Language.  For TAL, see the Zope Presentation Templates ZWiki:

    http://dev.zope.org/Wikis/DevSite/Projects/ZPT/FrontPage

It is not a Zope product nor is it designed exclusively to run inside
of Zope, but if you have a Zope checkout that includes
Products/ParsedXML, its Expat parser will be used.

Prerequisites
-------------

You need:

- A recent checkout of Zope2; don't forget to run the wo_pcgi.py
  script to compile everything.  (See above -- this is now optional.)

- A recent checkout of the Zope2 product ParsedXML, accessible
  throught <Zope2>/lib/python/Products/ParsedXML; don't forget to run
  the setup.py script to compiles Expat.  (Again, optional.)

- Python 1.5.2; the driver script refuses to work with other versions
  unless you specify the -n option; this is done so that I don't
  accidentally use Python 2.x features.

- Create a .path file containing proper module search path; it should
  point the <Zope2>/lib/python directory that you want to use.

How To Play
-----------

(Don't forget to edit .path, see above!)

The script driver.py takes an XML file with TAL markup as argument and
writes the expanded version to standard output.  The filename argument
defaults to tests/input/test01.xml.

Regression test
---------------

There are unit test suites in the 'tests' subdirectory; these can be
run with tests/run.py.  This should print the testcase names plus
progress info, followed by a final line saying "OK".  It requires that
../unittest.py exists.

There are a number of test files in the 'tests' subdirectory, named
tests/input/test<number>.xml and tests/input/test<number>.html.  The
Python script ./runtest.py calls driver.main() for each test file, and
should print "<file> OK" for each one.  These tests are also run as
part of the unit test suites, so tests/run.py is all you need.

What's Here
-----------

DummyEngine.py		simple-minded TALES execution engine
TALInterpreter.py	class to interpret intermediate code
TALGenerator.py		class to generate intermediate code
XMLParser.py		base class to parse XML, avoiding DOM
TALParser.py		class to parse XML with TAL into intermediate code
HTMLTALParser.py	class to parse HTML with TAL into intermediate code
HTMLParser.py		HTML-parsing base class
driver.py		script to demonstrate TAL expansion
timer.py		script to time various processing phases
setpath.py		hack to set sys.path and import ZODB
__init__.py		empty file that makes this directory a package
runtest.py		Python script to run file-comparison tests
ndiff.py		helper for runtest.py to produce diffs
tests/			drectory with test files and output
tests/run.py		Python script to run all tests

Author and License
------------------

This code is written by Guido van Rossum (project lead), Fred Drake,
and Tim Peters.  It is owned by Digital Creations and can be
redistributed under the Zope Public License.

TO DO
-----

(See also http://www.zope.org/Members/jim/ZPTIssueTracker .)

- Need to remove leading whitespace and newline when omitting an
  element (either through tal:replace with a value of nothing or
  tal:condition with a false condition).

- Empty TAL/METAL attributes are ignored: tal:replace="" is ignored
  rather than causing an error.

- HTMLTALParser.py and TALParser.py are silly names.  Should be
  HTMLTALCompiler.py and XMLTALCompiler.py (or maybe shortened,
  without "TAL"?)

- Should we preserve case of tags and attribute names in HTML?
