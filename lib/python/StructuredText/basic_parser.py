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

"""
class display does the basic traversal of a DOC/StructuredText
structure.
This is the process that would be needed for a parser,
such as HTML.
Commented are the steps for getting a basic parser built.
The basic steps

1. Must define in __init__ a self.types dictionary which
   has the names of structured text types as its keys and
   functions to handle the types as its values.

2. Must define a function for each type type to be interpreted.
   NOTE : The function names must match those in the self.types
   dictionary.

3. A means of traversing a DOC or StructuredText structure must
   be availabe.
   NOTE : Unless the format of the structures returned by StructuredText
   and DOC have been altered, it should suffice to un-comment the
   if else clause in the function loop.
   
   
"""

class display:

   """
   # here you would define your dictionary of 
   # types to define. Type_name should be
   # the string returned by the instance's .type()
   # call. The .str item is what raw strings are
   # added to.

   def __init__(self):
      self.str = ""
      self.types = {"type_name":def_name}
   
   # paragraph would receive raw strings
   # only and add them to self.str

   def paragraph(self,par):
      self.str = self.str + par

   # Here you would traverse the instance's
   # (in this case object) string through
   # the .string() call. The string can
   # consist of strings, instances, and lists only
   # (anything else is a mistake)
   # Will need a function like this for every type
   # value in the self.types dictionary

   def def_name(self,object):
      for item in object.string():
         if type(item).__name__   == "string":
            self.paragraph(item)
         elif type(item).__name__ == "list":
            self.loop(item)
         elif type(item).__name__ == "instance":
            self.types[item.type()](item)
   """

   def loop(self,object):

      print object

      """
      
      UNCOMMENT THIS IF ELSE CLAUSE
      
      # This traverse's either a raw_string,
      # which is sent to self.paragraph, or
      # a list (often from an instance's string)
      # which is traversed and the strings, lists,
      # and instance's are parsed

      if type(object) == "string":
         self.paragraph(object)
      else:
         for x in object:
            if type(x).__name__ == "string":
               self.paragraph(object)
            elif type(x).__name__ == "list":
               self.loop(x)
            elif type(x).__name__ == "instance":
               self.types[x.type()](object)
      """

   def call_loop(self,subs):
      
      """
      # call loop handles sub-paragraphs
      # y[0] is the original paragraph,
      # y[1] is a list of that paragraph's
      # sub-paragraphs
      """
      
      for y in subs:
         self.loop(y[0])
         if y[1]:
            self.call_loop(y[1])

   def __call__(self,struct):
      
      """
      # x[0] is the original paragraph,
      # x[1] is a list of that paragraph's
      # sub-paragraphs
      """
      
      for x in struct:
         self.loop(x[0])
         if x[1]:
            self.call_loop(x[1])
      """
      result   = self.str
      self.str = 0
      return result
      """
