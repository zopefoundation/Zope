"""
Transient object and transient object container interfaces.
"""

import Interface

class Transient(Interface.Base):
    def invalidate(self):
        """
        Invalidate (expire) the transient object.

        Causes the transient object container's "before destruct" method
        related to this object to be called as a side effect.
        """

    def getLastAccessed(self):
        """
        Return the time the transient object was last accessed in
        integer seconds-since-the-epoch form.
        """

    def setLastAccessed(self):
        """
        Cause the last accessed time to be set to now.
        """

    def getCreated(self):
        """
        Return the time the transient object was created in integer
        seconds-since-the-epoch form.
        """

class DictionaryLike(Interface.Base):
    def keys(self):
        """
        Return sequence of key elements.
        """

    def values(self):
        """
        Return sequence of value elements.
        """

    def items(self):
        """
        Return sequence of (key, value) elements.
        """

    def get(self, k, default='marker'):
        """
        Return value associated with key k.  If k does not exist and default
        is not marker, return default, else raise KeyError.
        """

    def has_key(self, k):
        """
        Return true if item referenced by key k exists.
        """

    def clear(self):
        """
        Remove all key/value pairs.
        """

    def update(self, d):
        """
        Merge dictionary d into ourselves.
        """

    # DictionaryLike does NOT support copy()

class ItemWithId(Interface.Base):
    def getId(self):
        """
        Returns a meaningful unique id for the object.
        """

class TTWDictionary(DictionaryLike, ItemWithId):
    def set(self, k, v):
        """
        Call __setitem__ with key k, value v.
        """

    def delete(self, k):
        """
        Call __delitem__ with key k.
        """

    def __guarded_setitem__(self, k, v):
        """
        Call __setitem__ with key k, value v.
        """

class ImmutablyValuedMappingOfPickleableObjects(Interface.Base):
    def __setitem__(self, k, v):
        """
        Sets key k to value v, if k is both hashable and pickleable and
        v is pickleable, else raise TypeError.
        """

    def __getitem__(self, k):
        """
        Returns the value associated with key k.

        Note that no guarantee is made to persist changes made to mutable
        objects obtained via __getitem__, even if they support the
        ZODB Persistence interface.  In order to ensure that changes to
        mutable values are persisted, you need to explicitly put the value back
        in to the mapping via __setitem__.
        """

    def __delitem__(self, k):
        """
        Remove the key/value pair related to key k.
        """

class HomogeneousItemContainer(Interface.Base):
    """
    An object which:
    1.  Contains zero or more subobjects, all of the same type.
    2.  Is responsible for the creation of its subobjects.
    3.  Allows for the access of a subobject by key.
    """
    def getSubobjectInterface(self):
        """
        Returns the interface object which must be supported by items added
        to or created by this container.
        """

    def get(self, k, default=None):
        """
        Return value associated with key k.  If value associated with k does
        not exist, return default.
        """

    def has_key(self, k):
        """
        Return true if container has value associated with key k, else
        return false.
        """

    def delete(self, k):
        """
        Delete value associated with key k, raise a KeyError if nonexistent.
        """

class StringKeyedHomogeneousItemContainer(HomogeneousItemContainer):
    def new(self, k):
        """
        Creates a new subobject of the type supported by this container
        with key "k" and returns it.

        If an object already exists in the container with key "k", a
        KeyError is raised.

        "k" must be a string, else a TypeError is raised.
        """

    def new_or_existing(self, k):
        """
        If an object already exists in the container with key "k", it
        is returned.

        Otherwiser, create a new subobject of the type supported by this
        container with key "k" and return it.

        "k" must be a string, else a TypeError is raised.
        """
    
class TransientItemContainer(Interface.Base):
    def setTimeoutMinutes(self, timeout_mins):
        """
        Set the number of minutes of inactivity allowable for subobjects
        before they expire.
        """

    def getTimeoutMinutes(self):
        """
        Return the number of minutes allowed for subobject inactivity
        before expiration.
        """

    def getAddNotificationTarget(self):
        """
        Returns the current 'after add' function, or None.
        """

    def setAddNotificationTarget(self, f):
        """
        Cause the 'after add' function to be 'f'.

        If 'f' is not callable and is a string, treat it as a Zope path to
        a callable function.

        'after add' functions need accept a single argument: 'item', which
        is the item being added to the container.
        """

    def getDelNotificationTarget(self):
        """
        Returns the current 'before destruction' function, or None.
        """

    def setDelNotificationTarget(self, f):
        """
        Cause the 'before destruction' function to be 'f'.

        If 'f' is not callable and is a string, treat it as a Zope path to
        a callable function.

        'before destruction' functions need accept a single argument: 'item',
        which is the item being destroyed.
        """

    def notifyAdd(self, item):
        """
        Calls the registered ExecuteAfterAdd function on item.

        Raises no errors (traps errors).
        """

    def notifyDestruct(self, item):
        """
        Calls the registered ExecuteBeforeDestruct function on item.

        Raises no errors (traps errors).
        """

