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

from string import join, split, find
import re, sys, ST

from HTMLClass import HTMLClass

ets = HTMLClass.element_types
ets.update({'StructuredTextImage': 'image'})      

class HTMLWithImages(HTMLClass):

    element_types = ets

    def document(self, doc, level, output):
        output('<html>\n')
        children=doc.getChildNodes()
        if (children and
            children[0].getNodeName() == 'StructuredTextSection'):
           output('<head>\n<title>%s</title>\n</head>\n' %
                  children[0].getChildNodes()[0].getNodeValue())
        output('<body>\n')
        for c in children:
           getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</body>\n')
        output('</html>\n')

    def image(self, doc, level, output):
       if hasattr(doc, 'key'):
          output('<a name="%s"></a>\n' % doc.key)
       output('<img src="%s" alt="%s">\n' % (doc.href, doc.getNodeValue()))
       if doc.getNodeValue() and hasattr(doc, 'key'):
           output('<p><b>Figure %s</b> %s</p>\n' % (doc.key, doc.getNodeValue()))

    def xref(self, doc, level, output):
        val = doc.getNodeValue()
        output('<a href="#ref%s">[%s]</a>' % (val, val) )







