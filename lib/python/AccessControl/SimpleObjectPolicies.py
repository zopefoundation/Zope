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
__doc__='''Collect rules for access to objects that don\'t have roles.

$Id: SimpleObjectPolicies.py,v 1.9 2001/11/28 15:50:51 matt Exp $''' 
__version__='$Revision: 1.9 $'[11:-2] 

_noroles=[] # this is imported from various places

import Record

# Allow access to unprotected attributes
Record.Record.__allow_access_to_unprotected_subobjects__=1

ContainerAssertions={
    type(()): 1,
    type([]): 1,
    type({}): 1,
    type(''): 1,
    type(u''): 1,
    }

class _dummy_class: pass

from DocumentTemplate.DT_Util import TemplateDict
# Temporarily create a DictInstance so that we can mark its type as
# being a key in the ContainerAssertions.
templateDict = TemplateDict()
try:
    dictInstance = templateDict(dummy=1)[0]
    if type(dictInstance) is not type(_dummy_class()):
        ContainerAssertions[type(dictInstance)]=1
except:
    # Hmm, this may cause _() and _.namespace() to fail.
    # What to do?
    pass

Containers=ContainerAssertions.get
