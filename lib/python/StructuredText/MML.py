#!/usr/local/bin/python -- # -*- python -*-
# $What$
'''
$Id: MML.py,v 1.1 1998/02/27 18:46:37 jim Exp $'''
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
# 

from StructuredText import * # :-)
	
def ctag(s):
    # Blech, wish we could use character tags
    if s is None: s=''
    s=gsub(strong,'\\1<bold>\\2<plain>\\3',s)
    s=gsub(code,  '\\1<family Courier>\\2<family Times>\\3',s)
    s=gsub(em,    '\\1<italic>\\2<plain>\\3',s)
    return join(map(strip,split(s,'\n')),'\n')

class MML(StructuredText):

    '''\
    An MML structured text formatter.
    '''\

    def __str__(self,
		):
	'''\
	Return an HTML string representation of the structured text data.

	'''
	s=self._str(self.structure,self.level)
	return s

    def ul(self, before, p, after):
	return ("%s\n\n<Bulleted>\n%s%s"
		% (before, ctag(p), after))

    def ol(self, before, p, after):
	return ("%s\n\n<Numbered>\n%s%s"
		% (before, ctag(p), after))

    def dl(self, before, t, d, after):
	return ("%s\n\n<Term>\n%s\n\n<Definition>\n%s%s" 
		% (before,ctag(t),ctag(d),after))

    def head(self, before, t, level, d):
	return ("%s\n\n<Heading%d>\n%s%s"
		% (before,level,ctag(t),d))

    def normal(self,before,p,after):
	return "%s\n\n<Body>\n%s%s" % (before, ctag(p), after)

    def pre(self,structure,r=None):
	if r is None: r=['']
	for s in structure:
	    for line in split(s[0],'\n'):
		r.append('\n<PRE>')
		r.append(line)
	    self.pre(s[1],r)
	return join(r,'\n')

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
#
# $Log: MML.py,v $
# Revision 1.1  1998/02/27 18:46:37  jim
# *** empty log message ***
#
# Revision 1.7  1997/12/12 15:39:54  jim
# Added level as argument for html_with_references.
#
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
