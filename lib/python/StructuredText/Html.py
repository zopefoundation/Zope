#!/usr/bin/env/python

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
