#!/usr/bin/env/python

from string import replace,split
import re

class HTML:

   def __init__(self):
      self.string    = ""
      self.level     = 1
      self.olevels   = []
      self.ulevels   = []
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

      """
      object is a header instance. Everything within
      this instance's string is also a header. Go through
      every item in the string an print out the appropriate
      info for each item and then close the header
      """

      head = "<h%s>" % self.level
      self.string = self.string + head
      for item in object.string():
         if type(item).__name__ == "list":
            self.loop(item)
         elif type(item).__name__ == "string":
            self.paragraph(item)
         elif type(item).__name__ == "instance":
            self.instance(item)
      head = "</h%s>" % self.level
      self.string = self.string + head
      
   def order_list(self,object):
      """
      object is an ordered list instance. Everything
      within is also part of an ordered list.
      """

      tmp = 1
      for x in self.olevels:
         if x == self.level:
            tmp = 0
      if tmp:
         self.olevels.append(self.level)
         self.string = self.string + "<ol>\n"

      self.string = self.string + "<li>"
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
      self.string = self.string + "</li>\n"

   def unorder_list(self,object):
      """
      object is an unordered list instance. Everything
      within is also part of an ordered list.
      """

      tmp = 1
      for x in self.ulevels:
         if x == self.level:
            tmp = 0
      if tmp:
         self.ulevels.append(self.level)
         self.string = self.string + "<ul>\n"

      self.string = self.string + "<li>"
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

      self.string = self.string + "</li>\n"

   def emphasize(self,object):
      """
      object is an emphasize instance. Everything
      within is also emphasized.
      """
            
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
      """
      object is a strong instance. Everything
      within is also part of an ordered list.
      """
      
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
      """
      object is a strong instance. Everything
      within is also part of an ordered list.
      """
      
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
      """
      The object's string should be a string, nothing more
      """
      
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
      """
      The object's string should be a string, nothing more
      """
      
      result = ""
      for x in object.string():
         result = result + x
      strings = split(result,",")
      strings[0] = replace(strings[0],'"','')
      result = "<a href=%s>%s</a>" % (strings[1],strings[0])
      self.string = self.string + result
      
   def description(self,object):
      """
      just print the damn thing out for now
      """
      
      result = ""
      for x in object.string():
         result = result + x
      result = replace(result,"\n","\n<br>")
      self.string = self.string + "<descr> " + result + " </descr>"

   def example(self,object):
      """
      An example object's string should be just a string an
      outputed as-is
      """

      result = ""
      for x in object.string():
         result = result + x
      
      result = replace(result,"\n","\n<br>")      
      result = replace(result,"'","")
      self.string = self.string + result

   def named_link(self,object):
      """
      The object's string should be a string, nothing more
      """
      
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
      object = replace(object,"\n","<br>\n")
      self.string = self.string + object

   def instance(self,object):
      if self.types.has_key(object.type()):
         self.types[object.type()](object)
      else:
         print "error, type not supported ", type(object)
      result = "%s,%s" % (object.string(),self.level)

   def loop(self,object):
      if type(object) == "string":
         self.paragraph(object)
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
         self.loop(y[0])
         if y[1]:
            self.level = self.level + 1
            self.call_loop(y[1])
            self.level = self.level - 1

   def __call__(self,struct):
      for x in struct:
         self.list_check(x[0])
         self.loop(x[0])
         if x[1]:
            self.level = self.level + 1
            self.call_loop(x[1])
            self.level = self.level - 1

      self.string = "<html>\n<body bgcolor='white' text='black'>\n" + self.string[:len(self.string)]
      result = self.string
      self.string = ""
      return result
