
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
    
