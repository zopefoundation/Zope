TAL - Template Attribute Language
---------------------------------

This is a prototype implementation of TAL, the Zope Template Attribute
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

- Edit the setpath.py script to set the proper module search path; the
  variable libPython should be set to the <Zope2>/lib/python directory
  that you want to use.  (Again, optional.)

How To Play
-----------

(If you want to use Zope, don't forget to edit setpath.py, see above!)

The script driver.py takes an XML file with TAL markup as argument and
writes the expanded version to standard output.  The filename argument
defaults to test/test1.xml.

Regression test
---------------

There are a number of test files in the test subdirectory, named
test/input/test<number>.xml and test/input/test<number>.html.  The
Python script ./runtest.py calls driver.main() for each test file, and
should print "<file> OK" for each one.

In addition, there are unit test suites in the test subdirectory;
these can be run with test/run.py.  This should print a number of
testcase names plus progress info, ending with a line saying "OK".
It requires that ../unittest.py exists.

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
runtest.py		Python script to run regression tests
ndiff.py		helper for runtest.py to produce diffs
test/			drectory with test files and output

Author and License
------------------

This code is written by Guido van Rossum (project lead), Fred Drake,
and Tim Peters.  It is owned by Digital Creations and can be
redistributed under the Zope Public License.

TO DO
-----

- Finish implementing insertStructure(): attribute replacement isn't
  implemented yet.

- TALInterpreter currently always uses an XML parser to parse inserted
  structure; it should use a parser appropriate to the mode.

- HTMLTALParser.py and TALParser.py are silly names.  Should be
  HTMLTALCompiler.py and XMLTALCompiler.py (or maybe shortened,
  without "TAL"?)

- Should we preserve case of tags and attribute names in HTML?

- Do we still need the HTML mode for TALInterpreter, which tries to
  generate HTML from an XML template?

- If use-macro fails, it seems to omit the entire macro except for
  slots, instead of leaving the existing text alone.

- We shouldn't be adding slashes to empty tags ('<br>' => '<br />'),
  and we definitely should not be abbreviating non-empty tags
  ('<td></td>' => '<td />').
