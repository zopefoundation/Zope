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


from HTMLClass import HTMLClass

ets = HTMLClass.element_types
ets.update({'StructuredTextImage': 'image'})

class HTMLWithImages(HTMLClass):

    element_types = ets


    def image(self, doc, level, output):
        if hasattr(doc, 'key'):
            output('<a name="%s"></a>\n' % doc.key)
        output('<img src="%s" alt="%s" />\n' % (doc.href, doc.getNodeValue()))
        if doc.getNodeValue() and hasattr(doc, 'key'):
            output('<p><b>Figure %s</b> %s</p>\n' % (doc.key, doc.getNodeValue()))
