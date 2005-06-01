##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Event test fixtures

$Id: subscriber.py 12915 2005-05-31 10:23:19Z philikon $
"""
class EventCatcher:
    def __init__(self):
        self._events = []
        
    def subscriber(self, event):
        self._events.append(event)

    def getEvents(self):
        return self._events

    def clear(self):
        self._events = []

objectEventCatcher = EventCatcher()
objectEventSubscriber = objectEventCatcher.subscriber

objectMovedEventCatcher = EventCatcher()
objectMovedEventSubscriber = objectMovedEventCatcher.subscriber

objectAddedEventCatcher = EventCatcher()
objectAddedEventSubscriber = objectAddedEventCatcher.subscriber

objectCopiedEventCatcher = EventCatcher()
objectCopiedEventSubscriber = objectCopiedEventCatcher.subscriber

objectRemovedEventCatcher = EventCatcher()
objectRemovedEventSubscriber = objectRemovedEventCatcher.subscriber

def clear():
    objectEventCatcher.clear()
    objectMovedEventCatcher.clear()
    objectAddedEventCatcher.clear()
    objectCopiedEventCatcher.clear()
    objectRemovedEventCatcher.clear()
    
