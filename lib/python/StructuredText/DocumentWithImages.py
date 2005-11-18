##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
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
    """ Document with images """

    text_types = [
       'doc_img',
       ] + DocumentClass.text_types


    def doc_img(
        self, s,
        expr1=re.compile('\"([ _a-zA-Z0-9*.:/;,\[\]\'\-\n\~]+)\":img:([a-zA-Z0-9%\_\-.:/\?=;,\n\~]+)').search,
        ):


        r=expr1(s)
        if r:
            startt, endt = r.span(1)
            starth, endh = r.span(2)
            start, end = r.span()
            return (StructuredTextImage(s[startt:endt], href=s[starth:endh]),
                    start, end)

        return None
