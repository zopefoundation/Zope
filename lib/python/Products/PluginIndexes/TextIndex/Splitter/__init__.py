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
#############################################################################

import os,sys,exceptions

availableSplitters = (
  ("ZopeSplitter" , "Zope Default Splitter"),
  ("ISO_8859_1_Splitter" , "Werner Strobls ISO-8859-1 Splitter"),
  ("UnicodeSplitter" , "Unicode-aware splitter")
)

splitterNames = map(lambda x: x[0],availableSplitters)

def getSplitter(name=None):

    if not name in splitterNames and name:
        raise exceptions.RuntimeError, "No such splitter '%s'" % name

    if not name: name = splitterNames[0]
    if not vars().has_key(name):
        exec( "from %s.%s import %s" % (name,name,name))

    return vars()[name]
