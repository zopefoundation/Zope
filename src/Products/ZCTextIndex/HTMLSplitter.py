##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import re

from zope.interface import implements

from Products.ZCTextIndex.ISplitter import ISplitter
from Products.ZCTextIndex.PipelineFactory import element_factory

class HTMLWordSplitter:

    implements(ISplitter)

    def process(self, text, wordpat=r"(?L)\w+"):
        splat = []
        for t in text:
            splat += self._split(t, wordpat)
        return splat

    def processGlob(self, text):
        # see Lexicon.globToWordIds()
        return self.process(text, r"(?L)\w+[\w*?]*")

    def _split(self, text, wordpat):
        text = text.lower()
        remove = [r"<[^<>]*>",
                  r"&[A-Za-z]+;"]
        for pat in remove:
            text = re.sub(pat, " ", text)
        return re.findall(wordpat, text)

element_factory.registerFactory('Word Splitter',
                                'HTML aware splitter',
                                HTMLWordSplitter)

if __name__ == "__main__":
    import sys
    splitter = HTMLWordSplitter()
    for path in sys.argv[1:]:
        f = open(path, "rb")
        buf = f.read()
        f.close()
        print path
        print splitter.process([buf])
