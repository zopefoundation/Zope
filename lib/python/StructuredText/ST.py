#!/usr/bin/env/python
##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

import re
from string import split,join,replace,expandtabs,strip

def indention(str):

   """ 
   Convert all tabs to the appropriate number of spaces.
   Find the number of leading spaces. If none, return 0
   """

   if str == '\n':
      return -1

   front = re.compile('( *)')
   m     = front.match(str)

   if m:
      start,end = m.span()    # find number of leading spaces
      return end-start
   else:
      return 0                # no leading spaces

def runner(struct,top,level,numbers):

   tmp = []
   for x in numbers:
      if level > x:
         tmp.append(x)

   numbers = tmp
   numbers.append(level)

   if len(numbers) == 1:
      return (struct,numbers)

   run = struct[top][1]
   if level == numbers[len(numbers)-1]:
      i = 1
      while i < level:         
         run = run[len(run)-1][1]
         i = i + 1
   else:
      i = 1
      while i <= level:
         run = run[len(run)-1][1]
         i = i + 1
   return run,numbers

def split_paragraphs(paragraphs):

   """
   each paragraph is denoted by the end of a line
   and a blank line before the beginning of a new
   paragraph
   """

   tmp   = ''
   par   = re.compile('\n[ ]*\n')
   
   if type(paragraphs).__name__ == "list":
      for paragraph in paragraphs:
         tmp = tmp + expandtabs(paragraph)
      paragraphs = par.split(tmp)
   elif type(paragraphs).__name__ == "string":
      paragraphs = par.split(expandtabs(paragraphs))
   else:
      print "paragraphs in unacceptable format, must be string or list"
      return []

   for i in range(len(paragraphs)):
      paragraphs[i] = paragraphs[i] + '\n\n'

   return paragraphs

def parent_level(levels, level):
   K = levels.keys()
   greatest = 0
   for key in K:
      if key > greatest and key < level:
         greatest = key
   return greatest

def find_level(levels,indention):
   K = levels.keys()
   for key in K:
      if levels[key] == indention:
         return key
   return -1

def StructuredText(paragraphs):

   """
   StructuredText accepts paragraphs, which is a list of 
   lines to be parsed. StructuredText creates a structure
   which mimics the structure of the paragraphs.
   Structure => [paragraph,[sub-paragraphs]]
   """

   current_level     = 0
   current_indent    = 0
   levels            = {0:0}
   ind               = []    # structure based on indention levels
   top               = -1    # which header are we under
   numbers           = [0]   # Which levels have paragraphs
   struct            = []    # the structure to be returned

   paragraphs = split_paragraphs(paragraphs)

   if not paragraphs:
      result = ["",[]]
      return result

   for paragraph in paragraphs:
      if paragraph == '\n':
         ind.append([-1, paragraph])
      else:
         ind.append([indention(paragraph), strip(paragraph)+"\n"])

   current_indent = indention(paragraphs[0])
   levels[0]      = current_indent

   for indent,paragraph in ind :
      if indent == 0:
         struct.append([paragraph,[]])
         current_level  = 0
         current_indent = 0
         numbers        = [0]
         levels         = {0:0}
         top            = top + 1
      elif indent == current_indent:
         run.append([paragraph,[]])
      elif indent > current_indent:
         current_level  = current_level + 1
         current_indent = indent
         numbers.append(current_level)
         levels[current_level] = indent
         run,numbers = runner(struct,top,current_level,numbers)
         run.append([paragraph,[]])
         levels[current_level] = indent
      elif indent < current_indent:
         l = parent_level(levels,current_level)
         if indent > 0 and indent < levels[0]:
            levels[0]      = indent
            current_indent = indent
            run,numbers    = runner(struct,top,current_level,numbers)
         elif find_level(levels,indent) != -1:
            current_level  = find_level(levels,indent)
            current_indent = indent
            run,numbers    = runner(struct,top,current_level,numbers)
            tmp   = {}
            K     = levels.keys()
            for key in K:
               if key <= current_level:
                  tmp[key] = levels[key]
            levels = tmp
         elif levels[current_level] > indent and levels[l] < indent:
            levels[current_level] = indent
            current_indent        = indent
            run,numbers           = runner(struct,top,current_level,numbers)
            current_level         = l
         else:
            tmp = {}
            j   = 0
            for i in range(current_level):
               if indent > levels[i]:
                  tmp[i] = levels[i]
               elif indent == levels[i]:
                  current_level  = i
                  current_indent = indent
                  run,numbers    = runner(struct,top,current_level,numbers)
            levels = tmp
         run.append([paragraph,[]])
   return struct

class doc_text:
   
   """
   doc_text is what a paragraph is considered to be until
   a structured_text type is found in the paragraph
   """
   
   def __init__(self,str=''):
      self.str = str

   def type(self,str=''):
      return 'text'
      
   def string(self):
      return  self.str

   def __getitem__(self,index):
     return self.str[index]

   def __call__(self,str,subs):
     return None

class doc_header:
   
   """
   This class is for header instances.
   The structure that doc_header matches is a single line
   paragraph whose sub-paragraphs are of a lower level.
   """
   
   def __init__(self,str=''):
      self.expr   = re.compile('[ a-zA-Z0-9.:/,-_*<>\?\'\"]+').match
      self.str    = [str]      # list things within this instance
      self.typ    = "header"   # what type is this expresion
      self.start  = 0          # start position of expr
      self.end    = 0          # end position of expr

   def type(self):
      return self.typ
         
   def string(self):
      return self.str

   def __getitem__(self,index):
      return self.str[index]

   def __call__(self,raw_string,subs):
      
      """
      The raw_string is checked to see if it matches the rules
      for this structured text expression. If the raw_string does,      
      it is parsed for the sub-string which matches and a doc_header
      instance is returned whose string is the matching substring.
      If raw_string does not match, nothing is returned.
      """
      lines = []
      tmp = split(raw_string, '\n')
      for i in range(len(tmp)):
         if tmp[i]:
            lines.append(tmp[i])
      if len(lines) > 1:
         return None
      if not subs:
         return None
      if self.expr(raw_string):
         start,end               = self.expr(raw_string).span()
         result                  = doc_header(raw_string[start:end])
         result.start,result.end = self.expr(raw_string).span()
         return result
      else:
         return None
   
   def span(self):
      return self.start,self.end

class doc_unorder_list:
   
   """
   This class matches for unordered list elements.
   """
   
   def __init__(self,str=''):
      self.expr   = re.compile('\s*(-\s+|\*\s+|o\s+)[ a-zA-Z0-9.:/,*_<>]+').match
      self.str    = [str]
      self.typ    = "unorder_list"
      self.start  = 0
      self.end    = 0

   def type(self):
      return self.typ

   def string(self):
      return self.str

   def __getitem__(self,index):
      return self.str[index]

   def __call__(self,raw_string,subs):
      
      """
      The raw_string is checked to see if it matches the rules
      for this structured text expression. If the raw_string does,      
      it is parsed for the sub-string which matches and a doc_unorder_list
      instance is returned whose string is the matching substring.
      If raw_string does not match, nothing is returned.
      """
      
      if self.expr(raw_string):
         result                     = doc_unorder_list(raw_string[0:len(raw_string)])
         result.start, result.end   = (0,len(raw_string))
         return result
      else: 
         return None

   def span(self):
      return self.start,self.end

class doc_order_list:
   def __init__(self,str=''):
      self.expr   = re.compile('\s*[0-9]+(?=s*|.)').match
      self.str    = [str]
      self.typ    = "order_list"

   def type(self):
      return self.typ

   def string(self):
      return self.str

   def __getitem__(self,index):
      return self.str[index]

   def __call__(self,raw_string,subs):      
      
      """
      The raw_string is checked to see if it matches the rules
      for this structured text expression. If the raw_string does,      
      it is parsed for the sub-string which matches and a doc_order_list
      instance is returned whose string is the matching substring.
      If raw_string does not match, nothing is returned.
      """

      if self.expr(raw_string):
         result                     = doc_order_list(raw_string[0:len(raw_string)])
         result.start, result.end   = (0,len(raw_string))
         return result
      else:
         return None

   def span(self):
      return self.start,self.end

class doc_example:
   def __init__(self,str=''):
      self.expr   = re.compile('\s*\'[ \na-zA-Z0-9.:/\-\_,*<>]+\'(?=s*)').search
      self.str    = [str]
      self.typ    = "example"
   
   def type(self):
      return self.typ

   def string(self):
      return self.str

   def __getitem__(self,index):
      return self.str[index]

   def __call__(self,raw_string,subs):
   
      """
      The raw_string is checked to see if it matches the rules
      for this structured text expression. If the raw_string does,      
      it is parsed for the sub-string which matches and a doc_example
      instance is returned whose string is the matching substring.
      If raw_string does not match, nothing is returned.
      """
      
      if self.expr(raw_string):
         start,end               = self.expr(raw_string).span()
         result                  = doc_example(raw_string[start:end])
         result.start,result.end = self.expr(raw_string).span()
         return result
      else:
         return None
   
   def span(self):
      return self.start,self.end

class doc_examples:
   def __init__(self,str=''):
      self.expr   = re.compile('(example|examples|::)\s+').search
      self.str    = [str]
      self.typ    = "example"

   def type(self):
      return self.typ
      
   def string(self):
      return self.str

   def __getitem__(self,index):
      return self.str[index]

   def __call__(self,raw_string,subs):
      
      
      """
      The raw_string is checked to see if it matches the rules
      for this structured text expression. If raw_string matches,
      all sub-paragraphs of the raw_string are turned into example
      paragraphs.
      If raw_string does not match, nothing is returned.
      """
      
      
      if self.expr(raw_string):
         for i in range(len(subs)):
            subs[i][0] = doc_example(subs[i][0])
      return None
         
   def span(self):
       return self.start,self.end

class doc_emphasize:
   def __init__(self,str=''):
      self.expr   = re.compile('\s*\*[ \na-zA-Z0-9.:/;,\'\"\?]+\*(?!\*|-)').search
      self.str    = [str]
      self.typ    = "emphasize"
         
   def type(self):
      return self.typ
      
   def string(self):
      return self.str

   def __getitem__(self,index):
      return self.str[index]

   def __call__(self,raw_string,subs):
   
      """
      The raw_string is checked to see if it matches the rules
      for this structured text expression. If the raw_string does,      
      it is parsed for the sub-string which matches and a doc_emphasize
      instance is returned whose string is the matching substring.
      If raw_string does not match, nothing is returned.
      """
      
      if self.expr(raw_string):
         start,end               = self.expr(raw_string).span()
         result                  = doc_emphasize(raw_string[start:end])
         result.start,result.end = self.expr(raw_string).span()
         return result
      else:
         return None
   
   def span(self):
      return self.start,self.end

class doc_strong:
   def __init__(self,str=''):
      self.expr   = re.compile('\s*\*\*[ \na-zA-Z0-9.:/;\-,!\?\'\"]+\*\*').search
      self.str    = [str]
      self.typ    = "strong"
      
   def type(self):
      return '%s' % self.typ
      
   def string(self):
      return self.str

   def __getitem__(self,index):
      return self.str[index]

   def __call__(self,raw_string,subs):
   
      """
      The raw_string is checked to see if it matches the rules
      for this structured text expression. If the raw_string does,
      it is parsed for the sub-string which matches and a doc_strong
      instance is returned whose string is the matching substring.
      If raw_string does not match, nothing is returned.
      """

      if self.expr(raw_string):
         start,end               = self.expr(raw_string).span()
         result                  = doc_strong(raw_string[start:end])
         result.start,result.end = self.expr(raw_string).span()
         return result
      else:
         return None
   
   def span(self):
      return self.start,self.end

class doc_underline:
   def __init__(self,str=''):
      self.expr   = re.compile('\s*_[ \na-zA-Z0-9.:/;,\'\"\?]+_').search
      self.str    = [str]
      self.typ    = "underline"

   def type(self):
      return self.typ

   def string(self):
      return self.str

   def __getitem__(self,index):
      return self.str[index]

   def __call__(self,raw_string,subs):
   
      """
      The raw_string is checked to see if it matches the rules
      for this structured text expression. If the raw_string does,      
      it is parsed for the sub-string which matches and a doc_underline
      instance is returned whose string is the matching substring.
      If raw_string does not match, nothing is returned.
      """
      
      if self.expr(raw_string):
         start,end               = self.expr(raw_string).span()
         result                  = doc_underline(raw_string[start:end])
         result.start,result.end = self.expr(raw_string).span()
         return result
      else:
         return None
   
   def span(self):
      return self.start,self.end

class doc_href1:
   def __init__(self,str=''):
      self.expr   = re.compile('\"[ a-zA-Z0-9.:/;,\n\~]+\":[a-zA-Z0-9.:/;,\n\~]+(?=(\s+|\.|\!|\?))').search
      self.str    = [str]
      self.typ    = "href1"

   def type(self):
      return '%s' % self.typ

   def string(self):
      return self.str

   def __getitem__(self,index):
      return self.str[index]

   def __call__(self,raw_string,subs):
   
      """
      The raw_string is checked to see if it matches the rules
      for this structured text expression. If the raw_string does,      
      it is parsed for the sub-string which matches and a doc_href1
      instance is returned whose string is the matching substring.
      If raw_string does not match, nothing is returned.
      """
      
      if self.expr(raw_string):
         start,end               = self.expr(raw_string).span()
         result                  = doc_href1(raw_string[start:end])
         result.start,result.end = self.expr(raw_string).span()
         return result
      else:
         return None
   
   def span(self):
      return self.start,self.end

class doc_href2:
   def __init__(self,str=''):
      self.expr   = re.compile('\"[ a-zA-Z0-9./:]+\",\s+[ a-zA-Z0-9@.:/;]+(?=(\s+|\.|\!|\?))').search
      self.str    = [str]
      self.typ    = "href2"

   def type(self):
      return self.typ

   def string(self):
      return self.str

   def __getitem__(self,index):
      return self.str[index]

   def __call__(self,raw_string,subs):
   
      """
      The raw_string is checked to see if it matches the rules
      for this structured text expression. If the raw_string does,      
      it is parsed for the sub-string which matches and a doc_href2
      instance is returned whose string is the matching substring.
      If raw_string does not match, nothing is returned.
      """
      
      if self.expr(raw_string):
         start,end               = self.expr(raw_string).span()
         result                  = doc_href2(raw_string[start:end])
         result.start,result.end = self.expr(raw_string).span()
         return result
      else:
         return None
   
   def span(self):
      return self.start,self.end

class doc_inner_link:
   def __init__(self,str=''):
      self.expr   = re.compile('(?!\.\.\s*)\[[a-zA-Z0-9-_()",.:/]+\]').search
      self.str    = [str]
      self.typ    = "inner_link"

   def type(self):
      return '%s' % self.typ

   def string(self):
      return self.str

   def __getitem__(self,index):
      return self.str[index]

   def __call__(self,raw_string,subs):

      """
      The raw_string is checked to see if it matches the rules
      for this structured text expression. If the raw_string does,
      it is parsed for the sub-string which matches and a doc_inner_link
      instance is returned whose string is the matching substring.
      If raw_string does not match, nothing is returned.
      """

      if self.expr(raw_string):
         start,end               = self.expr(raw_string).span()
         result                  = doc_inner_link(raw_string[start:end])
         result.start,result.end = self.expr(raw_string).span()
         return result
      else:
         return None
   
   def span(self):
      return self.start,self.end

class doc_named_link:
   def __init__(self,str=''):
      self.expr   = re.compile('\.\.\s+\[[a-zA-Z0-9-_()",.:/]+\]').search
      self.str    = [str]
      self.typ    = "named_link"

   def type(self):
      return self.typ

   def string(self):
      return self.str
      
   def __getitem__(self,index):
      return self.str[index]

   def __call__(self,raw_string,subs):
   
      """
      The raw_string is checked to see if it matches the rules
      for this structured text expression. If the raw_string does,      
      it is parsed for the sub-string which matches and a doc_named_link
      instance is returned whose string is the matching substring.
      If raw_string does not match, nothing is returned.
      """
      
      if self.expr(raw_string):
         start,end               = self.expr(raw_string).span()
         result                  = doc_named_link(raw_string[start:end])
         result.start,result.end = self.expr(raw_string).span()
         return result
      else:
         return None
   
   def span(self):
      return self.start,self.end

class doc_description:
   def __init__(self,str=''):
      self.expr   = re.compile('\s*[ a-zA-Z0-9.:/,;*<>]+--(?![ a-zA-Z0-9.:/,;]+)').search
      self.str    = [str]
      self.typ    = "description"

   def type(self):
      return self.typ

   def string(self):
      return self.str

   def __getitem__(self,index):
      return self.str[index]

   def __call__(self,raw_string,subs):
   
      """
      The raw_string is checked to see if it matches the rules
      for this structured text expression. If the raw_string does,      
      it is parsed for the sub-string which matches and a doc_description
      instance is returned whose string is the matching substring.
      If raw_string does not match, nothing is returned.
      """
      
      lines = split(raw_string,'\n')
      if len(lines) < 2:
         return None
      if lines[1] == '':
         return None
      if self.expr(raw_string):
         start,end               = self.expr(raw_string).span()
         result                  = doc_description(raw_string[start:end])
         result.start,result.end = self.expr(raw_string).span()
         return result
      else:
         return None
   
   def span(self):
      return self.start,self.end

class DOC:

   """
     Class instance calls [ex.=> x()] require a structured text
     structure. Doc will then parse each paragraph in the structure
     and will find the special structures within each paragraph.
     Each special structure will be stored as an instance. Special
     structures within another special structure are stored within
     the 'top' structure
        EX : '-underline this-' => would be turned into an underline
     instance. '-underline **this**' would be stored as an underline
     instance with a strong instance stored in its string
   """

   def __init__(self):
      self.types  = [doc_unorder_list(),
                     doc_order_list(),
                     doc_header(),
                     doc_examples(),
                     doc_example(),
                     doc_strong(),
                     doc_emphasize(),
                     doc_underline(),
                     doc_href1(),
                     doc_href2(),
                     doc_named_link(),
                     doc_inner_link(),
                     doc_description(),
                     doc_text()]
      self.string   = []   # list of paragraphs, after being parsed
      self.org      = []   # the original raw_string
      self.now      = []   # the strings current appearance
      self.struct   = []   # the structuredtext object with tagged instances
   
   def dont_check(self,object,expr,subs):
      if object.type() == "example":
         return 0
      if object.type() == "named_link" and expr.type() == "inner_link":
         return 0
      if object.type() == "order_list" and expr.type() == "header":
         return 0
      if object.type() == "unorder_list" and expr.type() == "header":
         return 0
      return 1

   def original(self,str):

      """
      Finds the original structure of a paragraph.
      str is now that paragraph after parsing
      """

      for x in str:
         if type(x).__name__ == "instance":
            self.now = self.now + [x]
            self.original(x.string())
         elif type(x).__name__ == "string":
            self.org = self.org + [x]
            self.now = self.now + [x]
         else:
            self.original(x)

   def final_check(self,str,expr,subs):

      """
      str is a list
      expr is the special type being searched for
      subs are the sub-paragraphs of str
      final_check puts the string back together and looks
      to see if there is an instance that envelopes another
      instance. EX : this paragraph ** is a ** header
      if str = ['this paragraph', <strong instance>, 'header']
      the result should be [<header instance>]. The header
      instance's string in this case should be the old value of str
      """

      self.original(str)

      spans      = []
      start      = 0
      end        = 0
      tmpstr     = ""

      """
      self.now also has the string associated with an instance,
      that string needs to be removed
      """

      i = 1

      while i < len(self.now):
         del self.now[i+1]
         i = i + 2

      """ 
      find the spans of all the elements in str
      """

      for x in self.org:
        end    = start + len(x)
        spans.append([start,end])
        start  = start + end
        tmpstr = tmpstr + x

      self.org = [];
      self.now = [];

   def parse(self,raw_string,expr,subs=[]):

      """
      Parse accepts a raw_string, an expr to test the raw_string,
      and the raw_string's subparagraphs.
      
      Parse will continue to search through raw_string until 
      all instances of expr in raw_string are found. 
      
      If no instances of expr are found, raw_string is returned.
      Otherwise a list of substrings and instances is returned
      """

      tmp = []   # the list to be returned if raw_string is split

      while expr(raw_string,subs):
         #an instance of expr was found
         t            = expr(raw_string,subs)
         start,end    = t.span()
         tmp.append(raw_string[0:start])
         tmp.append(t)
         raw_string   = raw_string[end:len(raw_string)]
      if tmp:
         #the string was broken into a list
         return tmp + [raw_string]
      else:
         #string did not change
         return raw_string

   def instance(self,object,expr,subs):

      """
      Receives an instance and an expression.
      Instance will go through the instance's
      string and will test the expression on each
      string item. Each string item in the instance's
      string will then be updated if necessary
      """
      
      if self.dont_check(object,expr,subs):
         for i in range(len(object.string())):
            if type(object.str[i]).__name__ == "string":
               object.str[i] = self.parse(object.str[i],expr,subs)
            elif type(object.str[i]).__name__ == "instance":
               if object.str[i].type() != "example":
                  self.instance(object.str[i],expr,subs)
               else:
                  object.str[i] = object[i].str

   def list(self,object,expr,subs):

      """
      Need to go through each item in a list.
      Lists are composed of strings
      """

      for i in range(len(object)):
         if type(object[i]).__name__ == "instance":
            if self.dont_check(object[i],expr,subs):
               self.instance(object[i],expr,subs)
            else:
               object[i] = object[i]
         elif type(object[i]).__name__ == "string":
            object[i] = self.parse(object[i], expr, subs)
         elif type(object[i]).__name__ == "list":
            self.list(object[i],expr,subs)

   def divide(self,object,expr,subs):

      item = object.str

      if type(item).__name__ == "list":
         self.list(item,expr,subs)
      elif type(item).__name__ == "instance":
         self.instance(item,expr,subs)
      elif type(item).__name__ == "string":
         item        = self.parse(item,expr,subs)
         object.str  = item
      else:
         print type(item).__name__ , " is not supported"

   def search(self,str,subs):

      str      = doc_text(str)   # a paragraph is text until proven guilty

      """
      Search the paragraph for each special structure
      """
      
      for expr in self.types:
         self.divide(str,expr,subs)

      result = str.str

      """
      need to make sure that their are no instances that were missed
      in the over-all structure
      """

      if type(result).__name__ == "list":
         for expr in self.types:
            self.final_check(result,expr,subs)

      return result
 
   def call_test(self,par,subs):
      tmp = self.search(par,subs)
      self.string.append(tmp)
      return tmp

   def call_loop(self,pars):
      for y in pars:
         if y[1]:
            y[0] = self.call_test(y[0],y[1])
            self.call_loop(y[1])
         else:
            y[0] = self.call_test(y[0],y[1])

   def __call__(self,struct):
      self.string = []
      for x in struct:
         x[0] = self.call_test(x[0],x[1])
         if x[1]:
            self.call_loop(x[1])
      self.struct = struct
      return self.struct
