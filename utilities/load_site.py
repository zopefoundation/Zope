##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""Load a Zope site from a collection of files or directories
"""

usage=""" [options] url file .....

    where options are:

      -D

         For HTML documents, replace the start of the content, up to
         and including the opening body tag with a DTML var tag that
         inserts the standard header. Also replace the closing body
         and html tag with a DTML var tag that inserts the standard
         footer.

      -I

         For each index.html, add an index_html that redirects.

      -p path

         Path to ZPublisher.  If not provided, load_site will
         make an attempt to figure it out.

      -u user:password

         Credentials

      -v

         Run in verbose mode.

      -9

         Use *old* zope method names.
"""

import sys, getopt, os, string
ServerError=''
verbose=0
old=0
doctor=0
index_html=0

def main():
    user, password = 'superuser', '123'
    opts, args = getopt.getopt(sys.argv[1:], 'p:u:DIv9')
    global verbose
    global old
    global doctor
    global index_html
    havepath=None
    for o, v in opts:
        if o=='-p':
            d, f = os.path.split(v)
            if f=='ZPublisher': sys.path.insert(0,d)
            else: sys.path.insert(0,v)
            havepath=1
        elif o=='-u':
            v = string.split(v,':')
            user, password = v[0], string.join(v[1:],':')
        elif o=='-D': doctor=1
        elif o=='-I': index_html=1
        elif o=='-v': verbose=1
        elif o=='-9': old=1

    if not args:
        print sys.argv[0]+usage
        sys.exit(1)

    if not havepath:
        here=os.path.split(sys.argv[0])[0]
        if os.path.exists(os.path.join(here,'ZPublisher')):
            sys.path.insert(0,here)
        else:
            here=os.path.split(here)[0]
            here=os.path.join(here,'lib','python')
            if os.path.exists(os.path.join(here,'ZPublisher')):
                sys.path.insert(0,here)
        

    url=args[0]
    files=args[1:]

    import ZPublisher.Client
    global ServerError
    ServerError=ZPublisher.Client.ServerError
    object=ZPublisher.Client.Object(url, username=user, password=password)

    for f in files: upload_file(object, f)

def call(f, *args, **kw):
    # Call a function ignoring redirect bci errors.
    try: apply(f,args, kw)
    except ServerError, v:
        if str(v)[:1] != '3':
            raise sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]

def upload_file(object, f):
    if os.path.isdir(f): return upload_dir(object, f)
    dir, name = os.path.split(f)
    root, ext = os.path.splitext(name)
    if ext in ('file', 'dir'): ext=''
    else:
        ext=string.lower(ext)
        if ext and ext[0] in '.': ext=ext[1:]
    if ext and globals().has_key('upload_'+ext):
        if verbose: print 'upload_'+ext, f
        return globals()['upload_'+ext](object, f)

    if verbose: print 'upload_file', f, ext
    call(object.manage_addFile, id=name, file=open(f,'rb'))

def upload_dir(object, f):
    if verbose: print 'upload_dir', f
    dir, name = os.path.split(f)
    call(object.manage_addFolder, id=name)
    object=object.__class__(object.url+'/'+name,
                            username=object.username,
                            password=object.password)
    for n in os.listdir(f):
        upload_file(object, os.path.join(f,n))

# ----- phd -----
# Modified by Oleg Broytmann <phd2@earthling.net>

from sgmllib import SGMLParser

def join_attrs(attrs):
   attr_list = []
   for attrname, value in attrs:
      attr_list.append('%s="%s"' % (attrname, string.strip(value)))

   if attr_list:
      s = " " + string.join(attr_list, " ")
   else:
      s = ""

   return s


class HeadParser(SGMLParser):
   def __init__(self):
      SGMLParser.__init__(self)

      self.seen_starthead = 0
      self.seen_endhead   = 0
      self.seen_startbody = 0

      self.head = ""
      self.title = ""
      self.accumulator = ""


   def handle_data(self, data):
      if data:
         self.accumulator = self.accumulator + data

   def handle_charref(self, ref):
       self.handle_data("&#%s;" % ref)

   def handle_entityref(self, ref):
       self.handle_data("&%s;" % ref)

   def handle_comment(self, data):
      if data:
         self.accumulator = self.accumulator + "<!--%s-->" % data


   def start_head(self, attrs):
      if not self.seen_starthead:
         self.seen_starthead = 1
         self.head = ""
         self.title = ""
         self.accumulator = ""

   def end_head(self):
      if not self.seen_endhead:
         self.seen_endhead = 1
         self.head = self.head + self.accumulator
         self.accumulator = ""


   def start_title(self, attrs):
      self.head = self.head + self.accumulator
      self.accumulator = ""

   def end_title(self):
      self.title = self.accumulator
      self.accumulator = ""


   def start_body(self, attrs):
      if not self.seen_startbody:
         self.seen_startbody = 1
         self.accumulator = ""

   def end_body(self): pass # Do not put </BODY> and </HTML>
   def end_html(self): pass # into output stream


   # Pass other tags unmodified
   def unknown_starttag(self, tag, attrs):
      self.accumulator = self.accumulator + "<%s%s>" % (string.upper(tag), join_attrs(attrs))

   def unknown_endtag(self, tag):
      self.accumulator = self.accumulator + "</%s>" % string.upper(tag)



def parse_html(infile):
   parser = HeadParser()

   while 1:
      line = infile.readline()
      if not line: break
      parser.feed(line)

   parser.close()
   infile.close()

   return (string.strip(parser.title), string.strip(parser.head),
           string.strip(parser.accumulator))


def upload_html(object, f):
    dir, name = os.path.split(f)
    f=open(f)

    if doctor:
        title, head, body = parse_html(f)
        if old:
            body = ("<!--#var standard_html_header-->\n\n" +
                    body + "\n\n<!--#var standard_html_footer-->")
        else:
            body = ("<dtml-var standard_html_header>\n\n" +
                    body + "\n\n<dtml-var standard_html_footer>")

    else:
        if old: f=f.read()
        title, head, body = '', '', f

    if old:
        call(object.manage_addDocument, id=name, file=body)
        if index_html and name in ('index.html', 'index.htm'):
            call(object.manage_addDocument, id='index_html',
                 file=('<!--#raise Redirect-->'
                       '<!--#var URL1-->/%s'
                       '<!--#/raise-->' % name
                       ))
    else:
        call(object.manage_addDTMLDocument, id=name, title=title, file=body)
        if index_html and name in ('index.html', 'index.htm'):
            call(object.manage_addDTMLMethod, id='index_html',
                 file=('<dtml-raise Redirect>'
                       '<dtml-var URL1>/%s'
                       '</dtml-raise>' % name
                       ))

    # Now add META and other tags as property
    if head:
      object=object.__class__(object.url+'/'+name,
                            username=object.username,
                            password=object.password)
      call(object.manage_addProperty,
           id="loadsite-head", type="text", value=head)

# ----- /phd -----
    
upload_htm=upload_html

def upload_dtml(object, f):
    dir, name = os.path.split(f)
    f=open(f)

    if old:
        f=f.read()
        call(object.manage_addDocument, id=name, file=f)
    else:
        call(object.manage_addDTMLMethod, id=name, file=f)
        

def upload_gif(object, f):
    dir, name = os.path.split(f)
    call(object.manage_addImage, id=name, file=open(f,'rb'))

upload_jpg=upload_gif
upload_png=upload_gif

if __name__=='__main__': main()


