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

import re
from DocumentClass import *

class StructuredTextImage(StructuredTextMarkup):
    "A simple embedded image"

class DocumentWithImages(DocumentClass):   
    """

    """


    text_types = [
       'doc_img',
       ] + DocumentClass.text_types


    def doc_img(
        self, s,
        expr1=re.compile('\"([ _a-zA-Z0-9*.:/;,\-\n\~]+)\":img:([a-zA-Z0-9\_\-.:/;,\n\~]+)').search,
        expr2=re.compile('\"([ _a-zA-Z0-9*.:/;,\-\n\~]+)\":img:([a-zA-Z0-9\_\-.:/;,\n\~]+):([a-zA-Z0-9\-.:/;,\n\~]+)').search
        ):

        r = expr2(s)
        if r:

            # Warning: the regex are getting confused when the string after :img:
            # is an URL containing ":" (Collector #2276)
            # Ugly workaround: check if have an absolute URL here. Not a cool solution,
            # but it works !

            if not r.group(2) in ['http','file','ftp']:

                 startt, endt = r.span(1)
                 startk, endk = r.span(2)
                 starth, endh = r.span(3)
                 start, end = r.span()
    
                 key = s[startk:endk]
            
                 return (StructuredTextImage(s[startt:endt], href=s[starth:endh], key=s[startk:endk]), 
                      start, end)

            
        r=expr1(s)
        if r:
            startt, endt = r.span(1)
            starth, endh = r.span(2)
            start, end = r.span()
            return (StructuredTextImage(s[startt:endt], href=s[starth:endh]),
                    start, end)

        return None

