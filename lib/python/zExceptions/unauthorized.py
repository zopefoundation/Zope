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
"""
$Id: unauthorized.py,v 1.4 2001/11/28 15:51:23 matt Exp $
"""

from types import StringType

class Unauthorized(Exception):
    """Some user wasn't allowed to access a resource"""

    def __init__(self, message=None, value=None, needed=None, name=None, **kw):
        """Possible signatures:

        Unauthorized()
        Unauthorized(message) # Note that message includes a space
        Unauthorized(name)
        Unauthorized(name, value)
        Unauthorized(name, value, needed)
        Unauthorized(message, value, needed, name)
        
        Where needed is a mapping objects with items represnting requirements
        (e.g. {'permission': 'add spam'}). Any extra keyword arguments
        provides are added to needed.
        """
        if name is None and (
            not isinstance(message, StringType) or len(message.split()) <= 1):
            # First arg is a name, not a message
            name=message
            message=None
            
        self.name=name
        self.message=message
        self.value=value

        if kw:
            if needed: needed.update(kw)
            else: needed=kw
            
        self.needed=needed

    def __str__(self):
        if self.message is not None: return self.message
        if self.name is not None:
            return ("You are not allowed to access %s in this context"
                    % self.name)
        elif self.value is not None:
            return ("You are not allowed to access %s in this context"
                    % self.getValueName(self.value))
                
                            
    def getValueName(self):
        v=self.value
        vname=getattr(v, '__name__', None)
        if vname: return vname
        c = getattr(v, '__class__', type(v))
        c = getattr(c, '__name__', 'object')
        return "a particular %s" % c
    
