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

from string import replace,split
import re

class HTML:

   def __init__(self):
      self.string    = ""
      self.level     = 1
      self.olevels   = []
      self.ulevels   = []
      self.par       = "off"
      self.endofpar  = re.compile("\n\s*\n").search
      self.self_par = ["header","order_list", "unorder_list"]
      self.types     = {"header":self.header,
                        "named_link":self.named_link,
                        "order_list":self.order_list,
                        "unorder_list":self.unorder_list,
                        "strong":self.strong,
                        "emphasize":self.emphasize,
                        "href1":self.href1,
                        "href2":self.href2,
                        "description":self.description,
                        "inner_link":self.inner_link,
                        "named_link":self.named_link,
                        "example":self.example,
                        "underline":self.underline}

   def list_check(self,object):

      def not_order_list(item):
         if type(item).__name__ == "list":
            for x in item:
               if type(x).__name__ == "instance":
                  if x.type() == "order_list":
                     return 0
         return 1

      def not_unorder_list(item):
         if type(item).__name__ == "list":
            for x in item:
               if type(x).__name__ == "instance":
                  if x.type() == "unorder_list":
                     return 0
         return 1

      tmp = []
      for x in self.olevels:
         if self.level < x:
            self.string = self.string + "</ol>\n"
         elif self.level == x and not_order_list(object):
            self.string = self.string + "</ol>\n"
         else:
            tmp.append(x)
      self.olevels = tmp
      tmp = []
      for x in self.ulevels:
         if self.level < x:
            self.string = self.string + "</ul>\n"
         elif self.level == x and not_unorder_list(object):
            self.string = self.string + "</ul>\n"
         else:
            tmp.append(x)
      self.ulevels = tmp      
      
   def header(self,object):
      head = "<h%s><p>" % self.level            
      self.string = self.string + head
      for item in object.string():
         if type(item).__name__ == "list":
            self.loop(item)
         elif type(item).__name__ == "string":
            self.paragraph(item)
         elif type(item).__name__ == "instance":
            self.instance(item)
      head = "</p></h%s>" % self.level
      self.string = self.string + head
      
   def order_list(self,object):
      tmp = 1
      for x in self.olevels:
         if x == self.level:
            tmp = 0
      if tmp:
         self.olevels.append(self.level)
         self.string = self.string + "<ol>\n"

      self.string = self.string + "<li><p>"
      for item in object.string():
         if type(item).__name__ == "list":
            for i in range(len(item)):
               if type(item[i]).__name__ == "string":
                  tmp         = re.compile('[ 0-9.]+').match
                  if tmp(item[i]):
                     start,end   = tmp(item[i]).span()
                     item[i]     = item[i][0:start] + item[i][end:len(item[i])]
            self.loop(item)
         elif type(item).__name__ == "string":
            tmp = re.compile('[0-9.]+').search
            start,end = tmp(item).span()
            item = item[end:len(item)]
            self.paragraph(item)
         elif type(item).__name__ == "instance":
            self.instance(item)
      self.string = self.string + "</p></li>\n"

   def unorder_list(self,object):
      tmp = 1
      for x in self.ulevels:
         if x == self.level:
            tmp = 0
      if tmp:
         self.ulevels.append(self.level)
         self.string = self.string + "<ul>\n"

      self.string = self.string + "<li><p>"
      for item in object.string():
         if type(item).__name__ == "list":
            for i in range(len(item)):
               if type(item[i]).__name__ == "string":
                  item[i] = replace(item[i],"-","")
            self.loop(item)
         elif type(item).__name__ == "string":
            item = replace(item,"-","")
            self.paragraph(item)
         elif type(item).__name__ == "instance":
            self.instance(item)

      self.string = self.string + "</p></li>\n"

   def emphasize(self,object):
      self.string = self.string + "<em>"
      for item in object.string():
         if type(item).__name__ == "list":
            self.loop(item)
         elif type(item).__name__ == "string":
            item = replace(item,'*','')
            self.paragraph(item)
         elif type(item).__name__ == "instance":
            self.instance(item)
      self.string = self.string + "</em>"

   def strong(self,object):
      self.string = self.string + "<strong>"
      for item in object.string():
         if type(item).__name__ == "list":
            self.loop(item)
         elif type(item).__name__ == "string":
            item = replace(item,'**','')
            self.paragraph(item)
         elif type(item).__name__ == "instance":
            self.instance(item)
      self.string = self.string + "</strong>"

   def underline(self,object):
      self.string = self.string + "<u>"
      for item in object.string():
         if type(item).__name__ == "list":
            self.loop(item)
         elif type(item).__name__ == "string":
            item = replace(item,'_','')
            self.paragraph(item)
         elif type(item).__name__ == "instance":
            self.instance(item)
      self.string = self.string + "</u>"

   def href1(self,object):
      result = ""
      for x in object.string():
         result = result + x
      strings = split(result, '":')
      strings[0] = replace(strings[0],'"','')
      result = replace(strings[1],"\n","\n<br>")
      result = "<a href=%s>%s</a>" % (strings[1],strings[0])
      result = replace(result,"\n","\n<br>")
      self.string = self.string + result

   def href2(self,object):
      result = ""
      for x in object.string():
         result = result + x
      strings = split(result,",")
      strings[0] = replace(strings[0],'"','')
      result = "<a href=%s>%s</a>" % (strings[1],strings[0])
      self.string = self.string + result
      
   def description(self,object):
      result = ""
      for x in object.string():
         result = result + x
      result = replace(result,"\n","\n<br>")
      self.string = self.string + "<dt> " + result + " </dt>"

   def example(self,object):
      result = ""
      for x in object.string():
         result = result + x
      
      result = replace(result,"\n","\n<br>")      
      result = replace(result,"'","")
      self.string = self.string + result

   def named_link(self,object):
      result = ""
      for x in object.string():
         result = result + x
      result = replace(result,".. ","")
      tmp = replace(result,"[","")
      tmp = replace(tmp,"]","")
      result = replace(result,"\n","\n<br>")
      result = "<a name=%s>%s</a>" % (tmp,result)
      self.string = self.string + result

   def inner_link(self,object):
      """
      The object's string should be a string, nothing more
      """

      result = ""
      for x in object.string():
         result = result + x
      tmp = replace(result,"[","")
      tmp = replace(tmp,"]","")
      result = replace(result,"\n","\n<br>")
      result = "<a href=#%s>%s</a>" % (tmp,result)
      self.string = self.string + result

   def paragraph(self,object):
      self.string = self.string + object

   def check_paragraph(self,object):
      if self.par == "off":
         if type(object).__name__ == "list":
            for x in object:
               if type(x).__name__ == "instance":
                  for y in self.self_par:
                     if x.type() == y:
                        return
         self.par    = "on"
         self.string = self.string + "<p>"
      elif self.par == "on":
         self.string = self.string + "</p>\n"
         self.par    = "off"
      
   def instance(self,object):
      if self.types.has_key(object.type()):
         self.types[object.type()](object)
      else:
         print "error, type not supported ", type(object)
      result = "%s,%s" % (object.string(),self.level)

   def loop(self,object):

      if type(object) == "string":
         self.paragraph(object)
      else:
         for x in object:
            if type(x).__name__ == "string":
               self.paragraph(x)
            elif type(x).__name__ == "list":
               self.loop(x)
            elif type(x).__name__ == "instance":
               self.instance(x)

   def call_loop(self,subs):
      for y in subs:
         self.list_check(y[0])
         self.check_paragraph(y[0])
         self.loop(y[0])
         if y[1]:
            self.level = self.level + 1
            self.call_loop(y[1])
            self.level = self.level - 1
         self.check_paragraph(y[0])

   def __call__(self,struct):
      for x in struct:
         self.list_check(x[0])
         self.check_paragraph(x[0])
         self.loop(x[0])
         self.check_paragraph(x[0])
         if x[1]:
            self.level = self.level + 1
            self.call_loop(x[1])
            self.level = self.level - 1
      result = self.string
      self.string = ""
      return result
