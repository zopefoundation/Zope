#!/usr/local/bin/python -- # -*- python -*-
# $What$
'''Structured Text Manipulation

Parse a structured text string into a form that can be used with 
structured formats, like html.

Structured text is text that uses indentation and simple
symbology to indicate the structure of a document.  

A structured string consists of a sequence of paragraphs separated by
one or more blank lines.  Each paragraph has a level which is defined
as the minimum indentation of the paragraph.  A paragraph is a
sub-paragraph of another paragraph if the other paragraph is the last
preceedeing paragraph that has a lower level.

Special symbology is used to indicate special constructs:

- A paragraph that begins with a '-', '*', or 'o' is treated as an
  unordered list (bullet) element.

- A paragraph that begins with a sequence of digits followed by a
  white-space character is treated as an ordered list element.

- A paragraph that begins with a sequence of sequences, where each
  sequence is a sequence of digits or a sequence of letters followed
  by a period, is treated as an ordered list element.

- A paragraph with a first line that contains some text, followed by
  some white-space and '--' is treated as
  a descriptive list element. The leading text is treated as the
  element title.

- Sub-paragraphs of a paragraph that ends in the word 'example' or the
  word 'examples', or '::' is treated as example code and is output as is.

- Text enclosed single quotes (with white-space to the left of the
  first quote and whitespace or puctuation to the right of the second quote)
  is treated as example code.

- Text surrounded by '*' characters (with white-space to the left of the
  first '*' and whitespace or puctuation to the right of the second '*')
  is emphasized.

- Text surrounded by '**' characters (with white-space to the left of the
  first '**' and whitespace or puctuation to the right of the second '**')
  is made strong.

$Id: StructuredText.py,v 1.6 1997/12/12 15:27:25 jim Exp $'''
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
# $Log: StructuredText.py,v $
# Revision 1.6  1997/12/12 15:27:25  jim
# Added additional pattern matching for HTML references.
#
# Revision 1.5  1997/03/08 16:01:03  jim
# Moved code to recognize: "foo bar", url.
# into object initializer, so it gets applied in all cases.
#
# Revision 1.4  1997/02/17 23:36:35  jim
# Added support for "foo title", http:/foohost/foo
#
# Revision 1.3  1996/12/06 15:57:37  jim
# Fixed bugs in character tags.
#
# Added -t command-line option to generate title if:
#
#    - The first paragraph is one line (i.e. a heading) and
#
#    - All other paragraphs are indented.
#
# Revision 1.2  1996/10/28 13:56:02  jim
# Fixed bug in ordered lists.
# Added option for either HTML-style headings or descriptive-list style
# headings.
#
# Revision 1.1  1996/10/23 14:00:45  jim
# *** empty log message ***
#
#
# 

import regex, regsub
from regsub import gsub

indent_tab  =regex.compile('\(\n\|^\)\( *\)\t')
indent_space=regex.compile('\n\( *\)')
paragraph_divider=regex.compile('\(\n *\)+\n')

def untabify(aString):
    '''\
    Convert indentation tabs to spaces.
    '''
    result=''
    rest=aString
    while 1:
	start=indent_tab.search(rest)
	if start >= 0:
	    lnl=len(indent_tab.group(1))
	    indent=len(indent_tab.group(2))
	    result=result+rest[:start]
	    rest="\n%s%s" % (' ' * ((indent/8+1)*8),
			     rest[start+indent+1+lnl:])
	else:
	    return result+rest

def indent_level(aString):
    '''\
    Find the minimum indentation for a string, not counting blank lines.
    '''
    start=0
    text='\n'+aString
    indent=l=len(text)
    while 1:
	start=indent_space.search(text,start)
	if start >= 0:
	    i=len(indent_space.group(1))
	    start=start+i+1
	    if start < l and text[start] != '\n':	# Skip blank lines
		if not i: return (0,aString)
		if i < indent: indent = i
	else:
	    return (indent,aString)

def paragraphs(list,start):
    l=len(list)
    level=list[start][0]
    i=start+1
    while i < l and list[i][0] > level:	i=i+1
    return i-1-start

def structure(list):
    if not list: return []
    i=0
    l=len(list)
    r=[]
    while i < l:
	sublen=paragraphs(list,i)
	i=i+1
	r.append((list[i-1][1],structure(list[i:i+sublen])))
	i=i+sublen
    return r

bullet=regex.compile('[ \t\n]*[o*-][ \t\n]+\([^\0]*\)')
example=regex.compile('[\0- ]examples?:[\0- ]*$')
dl=regex.compile('\([^\n]+\)[ \t]+--[ \t\n]+\([^\0]*\)')
nl=regex.compile('\n')
ol=regex.compile('[ \t]*\(\([0-9]+\|[a-zA-Z]+\)[.)]\)+[ \t\n]+\([^\0]*\|$\)')
olp=regex.compile('[ \t]*([0-9]+)[ \t\n]+\([^\0]*\|$\)')



class StructuredText:

    '''\
    Model text as structured collection of paragraphs.

    Structure is implied by the indentation level.

    This class is intended as a base classes that do actual text
    output formatting.
    '''

    def __init__(self,aStructuredString, level=0):
	'''\
	Convert a string containing structured text into a structured text object.

	Aguments:

	  aStructuredString -- The string to be parsed.
	  level -- The level of top level headings to be created.
	'''

	aStructuredString = gsub(
	    '\"\([^\"\0]+\)\":'            # title part
	    '\([-:a-zA-Z0-9_,./?=@]+\)'  # URL
	    '\(,\|\([.:?;]\)\)'                   # trailing puctuation
	    '\([\0- ]\)',                         # trailing space
	    '<a href="\\2">\\1</a>\\4\\5',
	    aStructuredString)

	aStructuredString = gsub(
	    '\"\([^\"\0]+\)\",[\0- ]+'            # title part
	    '\([a-zA-Z]+:[-:a-zA-Z0-9_,./?=@]+\)'  # URL
	    '\(,\|\([.:?;]\)\)'                   # trailing puctuation
	    '\([\0- ]\)',                         # trailing space
	    '<a href="\\2">\\1</a>\\4\\5',
	    aStructuredString)

	self.level=level
	paragraphs=regsub.split(untabify(aStructuredString),paragraph_divider)
	paragraphs=map(indent_level,paragraphs)

	self.structure=structure(paragraphs)


    def __str__(self):
	return str(self.structure)


ctag_prefix="\([\0- (]\|^\)"
ctag_suffix="\([\0- ,.:;!?)]\|$\)"
ctag_middle="[%s]\([^\0- %s][^%s]*[^\0- %s]\|[^%s]\)[%s]"
ctag_middl2="[%s][%s]\([^\0- %s][^%s]*[^\0- %s]\|[^%s]\)[%s][%s]"
em    =regex.compile(ctag_prefix+(ctag_middle % (("*",)*6) )+ctag_suffix)
strong=regex.compile(ctag_prefix+(ctag_middl2 % (("*",)*8))+ctag_suffix)
code  =regex.compile(ctag_prefix+(ctag_middle % (("\'",)*6))+ctag_suffix)
	
def ctag(s):
    if s is None: s=''
    s=gsub(strong,'\\1<strong>\\2</strong>\\3',s)
    s=gsub(code,  '\\1<code>\\2</code>\\3',s)
    s=gsub(em,    '\\1<em>\\2</em>\\3',s)
    return s	

class HTML(StructuredText):

    '''\
    An HTML structured text formatter.
    '''\

    def __str__(self,
		extra_dl=regex.compile("</dl>\n<dl>"),
		extra_ul=regex.compile("</ul>\n<ul>"),
		extra_ol=regex.compile("</ol>\n<ol>"),
		):
	'''\
	Return an HTML string representation of the structured text data.

	'''
	s=self._str(self.structure,self.level)
	s=gsub(extra_dl,'\n',s)
	s=gsub(extra_ul,'\n',s)
	s=gsub(extra_ol,'\n',s)
	return s

    def ul(self, before, p, after):
	if p: p="<p>%s</p>" % ctag(p)
	return ('%s<ul><li>%s\n%s\n</ul>\n'
		% (before,p,after))

    def ol(self, before, p, after):
	if p: p="<p>%s</p>" % ctag(p)
	return ('%s<ol><li>%s\n%s\n</ol>\n'
		% (before,p,after))

    def dl(self, before, t, d, after):
	return ('%s<dl><dt>%s<dd><p>%s</p>\n%s\n</dl>\n'
		% (before,ctag(t),ctag(d),after))

    def head(self, before, t, level, d):
	if level > 0 and level < 6:
	    return ('%s<h%d>%s</h%d>\n%s\n'
		    % (before,level,ctag(t),level,d))
	    
	t="<p><strong>%s</strong><p>" % t
	return ('%s<dl><dt>%s\n<dd>%s\n</dl>\n'
	        % (before,ctag(t),d))

    def normal(self,before,p,after):
	return '%s<p>%s</p>\n%s\n' % (before,ctag(p),after)

    def _str(self,structure,level):
	r=''
	for s in structure:
	    # print s[0],'\n', len(s[1]), '\n\n'
	    if bullet.match(s[0]) >= 0:
		p=bullet.group(1)
		r=self.ul(r,p,self._str(s[1],level))
	    elif ol.match(s[0]) >= 0:
		p=ol.group(3)
		r=self.ol(r,p,self._str(s[1],level))
	    elif olp.match(s[0]) >= 0:
		p=olp.group(1)
		r=self.ol(r,p,self._str(s[1],level))
	    elif dl.match(s[0]) >= 0:
		t,d=dl.group(1,2)
		r=self.dl(r,t,d,self._str(s[1],level))
	    elif example.search(s[0]) >= 0 and s[1]:
		# Introduce an example, using pre tags:
		r=self.normal(r,s[0],self.pre(s[1]))
	    elif s[0][-2:]=='::' and s[1]:
		# Introduce an example, using pre tags:
		r=self.normal(r,s[0][:-1],self.pre(s[1]))
	    elif nl.search(s[0]) < 0 and s[1] and s[0][-1:] != ':':
		# Treat as a heading
		t=s[0]
		r=self.head(r,t,level,
			    self._str(s[1],level and level+1))
	    else:
		r=self.normal(r,s[0],self._str(s[1],level))
	return r

    def pre(self,structure,tagged=0):
	if not structure: return ''
	if tagged:
	    r=''
	else:
	    r='<PRE>\n'
	for s in structure:
	    r="%s%s\n\n%s" % (r,html_quote(s[0]),self.pre(s[1],1))
	if not tagged: r=r+'</PRE>\n'
	return r
	

def html_quote(v,
	       character_entities=(
		       (regex.compile('&'), '&amp;'),
		       (regex.compile("<"), '&lt;' ),
		       (regex.compile(">"), '&gt;' ),
		       (regex.compile('"'), '&quot;'))): #"
        text=str(v)
	for re,name in character_entities:
	    text=gsub(re,name,text)
	return text

def html_with_references(text):
    text = gsub(
	'[\0\n].. \[\([-_0-9_a-zA-Z-]+\)\]',
	'\n  <a name="\\1">[\\1]</a>',
	text)
    
    text = gsub(
	'\([\0- ,]\)\[\([0-9_a-zA-Z-]+\)\]\([\0- ,.:]\)',
	'\\1<a href="#\\2">[\\2]</a>\\3',
	text)
    
    text = gsub(
	'\([\0- ,]\)\[\([^]]+\)\.html\]\([\0- ,.:]\)',
	'\\1<a href="\\2.html">[\\2]</a>\\3',
	text)

    return HTML(text,level=1)
    

def main():
    import sys, getopt

    opts,args=getopt.getopt(sys.argv[1:],'tw')

    if args:
	[infile]=args
	s=open(infile,'r').read()
    else:
	s=sys.stdin.read()

    if opts:
	import regex, string, regsub

	if filter(lambda o: o[0]=='-w', opts):
	    print 'Content-Type: text/html\n'

	if s[:2]=='#!': s=regsub.sub('^#![^\n]+','',s)

	r=regex.compile('\([\0-\n]*\n\)')
	if r.match(s) >= 0:
	    s=s[len(r.group(1)):]
	s=str(html_with_references(s))
	if s[:4]=='<h1>':
	    t=s[4:string.find(s,'</h1>')]
	    s='''<html><head><title>%s</title>
	    </head><body>
	    %s
	    </body></html>
	    ''' % (t,s)
	print s
    else:
	print html_with_references(s)

if __name__=="__main__": main()
