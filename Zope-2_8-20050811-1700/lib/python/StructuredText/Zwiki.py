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

from Html   import HTML
from ST     import DOC
import re

"""
This is the new structured text type.
"""

class Zwiki_Title:
    def __init__(self,str=''):
        self.expr1   = re.compile('([A-Z]+[A-Z]+[a-zA-Z]*)').search
        self.expr2   = re.compile('([A-Z]+[a-z]+[A-Z]+[a-zA-Z]*)').search
        self.str    = [str]
        self.typ    = "Zwiki_Title"

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

        if self.expr1(raw_string):
            start,end               = self.expr1(raw_string).span()
            result                  = Zwiki_Title(raw_string[start:end])
            result.start,result.end = self.expr1(raw_string).span()
            return result
        elif self.expr2(raw_string):
            start,end               = self.expr2(raw_string).span()
            result                  = Zwiki_Title(raw_string[start:end])
            result.start,result.end = self.expr2(raw_string).span()
            return result
        else:
            return None

    def span(self):
        return self.start,self.end

class Zwiki_doc(DOC):

    def __init__(self):
        DOC.__init__(self)
        """
        Add the new type to self.types
        """
        self.types.append(Zwiki_Title())

class Zwiki_parser(HTML):
    def __init__(self):
        HTML.__init__(self)
        self.types["Zwiki_Title"] = self.zwiki_title

    def zwiki_title(self,object):
        result = ""
        for x in object.string():
            result = result + x
        result = "<a href=%s>%s</a>" % (result,result)
        #result = "<dtml-wikiname %s>" % result
        self.string = self.string + result
