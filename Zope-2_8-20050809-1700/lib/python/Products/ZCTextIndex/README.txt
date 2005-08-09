ZCTextIndex
===========

This product is a replacement for the full text indexing facility of
ZCatalog.  Specifically, it is an alternative to
PluginIndexes/TextIndex.

Advantages of using ZCTextIndex over TextIndex:

- A new query language, supporting both explicit and implicit Boolean
  operators, parentheses, globbing, and phrase searching.  Apart from
  explicit operators and globbing, the syntax is roughly the same as
  that popularized by Google.

- A more refined scoring algorithm, resulting in better selectiveness:
  it's much more likely that you'll find the document you are looking
  for among the first few highest-ranked results.

- Actually, ZCTextIndex gives you a choice of two scoring algorithms
  from recent literature: the Cosine ranking from the Managing
  Gigabytes book, and Okapi from more recent research papers.  Okapi
  usually does better, so it is the default (but your milage may
  vary).

- A redesigned Lexicon, using a pipeline architecture to split the
  input text into words.  This makes it possible to mix and match
  pipeline components, e.g. you can choose between an HTML-aware
  splitter and a plain text splitter, and additional components can be
  added to the pipeline for case folding, stopword removal, and other
  features.  Enough example pipeline components are provided to get
  you started, and it is very easy to write new components.

Performance is roughly the same as for TextIndex, and we're expecting
to make tweaks to the code that will make it faster.

This code can be used outside of Zope too; all you need is a
standalone ZODB installation to make your index persistent.  Several
functional test programs in the tests subdirectory show how to do
this, for example mhindex.py, mailtest.py, indexhtml.py, and
queryhtml.py.

See the online help for how to use ZCTextIndex within Zope.  (Included
in the subdirectory "help".)


Code overview
-------------

ZMI interface:

__init__.py			ZMI publishing code
ZCTextIndex.py			pluggable index class
PipelineFactory.py		ZMI helper to configure the pipeline

Indexing:

BaseIndex.py			common code for Cosine and Okapi index
CosineIndex.py			Cosine index implementation
OkapiIndex.py			Okapi index implementation
okascore.c			C implementation of scoring loop

Lexicon:

Lexicon.py			lexicon and sample pipeline elements
HTMLSplitter.py			HTML-aware splitter
StopDict.py			list of English stopwords
stopper.c			C implementation of stop word remover

Query parser:

QueryParser.py			parse a query into a parse tree
ParseTree.py			parse tree node classes and exceptions

Utilities:

NBest.py			find N best items in a list without sorting
SetOps.py			efficient weighted set operations
WidCode.py			list compression allowing phrase searches
RiceCode.py			list compression code (as yet unused)

Interfaces (these speak for themselves):

IIndex.py
ILexicon.py
INBest.py
IPipelineElement.py
IPipelineElementFactory.py
IQueryParseTree.py
IQueryParser.py
ISplitter.py

Subdirectories:

dtml				ZMI templates
help				ZMI help files
tests				unittests and some functional tests/examples
www				images used in the ZMI


Tests
-----

Functional tests and helpers:

hs-tool.py			helper to interpret hotshot profiler logs
indexhtml.py			index a collection of HTML files
mailtest.py			index and query a Unix mailbox file
mhindex.py			index and query a set of MH folders
python.txt			output from benchmark queries
queryhtml.py			query an index created by indexhtml.py
wordstats.py			dump statistics about each indexed word

Unit tests (these speak for themselves):

testIndex.py			
testLexicon.py
testNBest.py
testPipelineFactory.py
testQueryEngine.py
testQueryParser.py
testSetOps.py
testStopper.py
testZCTextIndex.py
