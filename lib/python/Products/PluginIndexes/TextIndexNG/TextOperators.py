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
#############################################################################


class Op:
    """ TextIndex operator class """

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name
    __str__ = __repr__



AndNot      = Op('andnot')
And         = Op('and')
Or          = Op('or')
Near        = Op('...')

operator_dict = {
    'andnot': AndNot, 
    'and':    And, 
    'or':     Or,
    '...':    Near, 
    'near':   Near,
    AndNot:   AndNot, 
    And:      And, 
    Or:       Or, 
    Near:     Near
}

QueryError    = 'TextIndex.QueryError'
