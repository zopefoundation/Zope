##########################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##########################################################################
"""
Transient Objects

  TransientObjectContainers are objects which contain zero or more
  TransientObjects.  They implement the following interfaces:

    - ItemWithId

    - StringKeyedHomogenousItemContainer

    - TransientItemContainer

  In particular, one uses the 'new_or_existing' method on
  TransientObjectContainers to retrieve or create a TransientObject
  based on a given string key.

  If add or delete notifications are registered with the container,
  they will be called back when items in the container are added or
  deleted, with the item and the container as arguments.  The
  callbacks may be registered either as bound methods, functions, or
  physical paths to Zope Script (Python Script or External Method)
  objects (e.g. '/some/resolvable/script/name').  In any of these
  cases, the delete and add notifications will be called with
  arguments allowing the callbacks to operate on data representing the
  state of the transient object at the moment of addition or deletion
  (see setAddNotificationTarget and setDelNotificationTarget below).

  TransientObjects are containerish items held within
  TransientObjectContainers and they implement the following
  interfaces:

    - ItemWithId

    - Transient

    - DictionaryLike

    - TTWDictionary

    - ImmutablyValuedMappingOfPickleableObjects

  Of particular importance is the idea that TransientObjects do not
  offer the contract of "normal" ZODB container objects; mutations
  made to items which are contained within a TransientObject cannot be
  expected to persist.  Developers need explicitly resave the state of
  a subobject of a TransientObject by placing it back into the
  TransientObject via the TransientObject.__setitem__ or .set methods.
  This requirement is due to the desire to allow people to create
  alternate TransientObject implementations that are *not* based on
  the ZODB.  Practically, this means that when working with a
  TransientObject which contains mutable subobjects (even if they
  inherit from Persistence.Persistent), you *must* resave them back
  into the TransientObject.  For example::

    class Foo(Persistence.Persistent):
        pass

    transient_object = transient_data_container.new('t')
    foo = transient_object['foo'] = Foo()
    foo.bar = 1
    # the following is *necessary* to repersist the data
    transient_object['foo'] = foo
  """

from zope.interface import Interface

class Transient(Interface):
    def invalidate():
        """
        Invalidate (expire) the transient object.

        Causes the transient object container's "before destruct" method
        related to this object to be called as a side effect.
        """

    def isValid():
        """
        Return true if transient object is still valid, false if not.
        A transient object is valid if its invalidate method has not been
        called.
        """

    def getLastAccessed():
        """
        Return the time the transient object was last accessed in
        integer seconds-since-the-epoch form.  Last accessed time
        is defined as the last time the transient object's container
        "asked about" this transient object.
        """

    def setLastAccessed():
        """
        Cause the last accessed time to be set to now.
        """

    def getLastModified():
        """
        Return the time the transient object was last modified in
        integer seconds-since-the-epoch form.  Modification generally implies
        a call to one of the transient object's __setitem__ or __delitem__
        methods, directly or indirectly as a result of a call to
        update, clear, or other mutating data access methods.
        """

    def setLastModified():
        """
        Cause the last modified time to be set to now.
        """

    def getCreated():
        """
        Return the time the transient object was created in integer
        seconds-since-the-epoch form.
        """

    def getContainerKey():
        """
        Return the key under which the object was placed in its
        container.
        """

class DictionaryLike(Interface):
    def keys():
        """
        Return sequence of key elements.
        """

    def values():
        """
        Return sequence of value elements.
        """

    def items():
        """
        Return sequence of (key, value) elements.
        """

    def get(k, default='marker'):
        """
        Return value associated with key k.  Return None or default if k
        does not exist.
        """

    def has_key(k):
        """
        Return true if item referenced by key k exists.
        """

    def clear():
        """
        Remove all key/value pairs.
        """

    def update(d):
        """
        Merge dictionary d into ourselves.
        """

    # DictionaryLike does NOT support copy()

class ItemWithId(Interface):
    def getId():
        """
        Returns a meaningful unique id for the object.  Note that this id
        need not the key under which the object is stored in its container.
        """

class TTWDictionary(DictionaryLike, ItemWithId):
    def set(k, v):
        """
        Call __setitem__ with key k, value v.
        """

    def delete(k):
        """
        Call __delitem__ with key k.
        """

    def __guarded_setitem__(k, v):
        """
        Call __setitem__ with key k, value v.
        """

class ImmutablyValuedMappingOfPickleableObjects(Interface):
    def __setitem__(k, v):
        """
        Sets key k to value v, if k is both hashable and pickleable and
        v is pickleable, else raise TypeError.
        """

    def __getitem__(k):
        """
        Returns the value associated with key k.

        Note that no guarantee is made to persist changes made to mutable
        objects obtained via __getitem__, even if they support the ZODB
        Persistence interface.  In order to ensure that changes to mutable
        values are persisted, you need to explicitly put the value back in
        to the mapping via __setitem__.
        """

    def __delitem__(k):
        """
        Remove the key/value pair related to key k.
        """

class HomogeneousItemContainer(Interface):
    """
    An object which:
     1.  Contains zero or more subobjects, all of the same type.
     2.  Is responsible for the creation of its subobjects.
     3.  Allows for the access of a subobject by key.
    """
    def get(k, default=None):
        """
        Return value associated with key k via __getitem__.  If value
        associated with k does not exist, return default.

        Returned item is acquisition-wrapped in self unless a default
        is passed in and returned.
        """

    def has_key(k):
        """
        Return true if container has value associated with key k, else
        return false.
        """

class StringKeyedHomogeneousItemContainer(HomogeneousItemContainer):
    def new(k):
        """
        Creates a new subobject of the type supported by this container
        with key "k" and returns it.

        If an object already exists in the container with key "k", a
        KeyError is raised.

        "k" must be a string, else a TypeError is raised.

        If the container is 'full', a MaxTransientObjectsExceeded exception
        will be raised.

        Returned object is acquisition-wrapped in self.
        """

    def new_or_existing(k):
        """
        If an object already exists in the container with key "k", it
        is returned.

        Otherwise, create a new subobject of the type supported by this
        container with key "k" and return it.

        "k" must be a string, else a TypeError is raised.

        If a new object needs to be created and the container is 'full',
        a MaxTransientObjectsExceeded exception will be raised.

        Returned object is acquisition-wrapped in self.
        """

class TransientItemContainer(Interface):
    def setTimeoutMinutes(timeout_mins):
        """
        Set the number of minutes of inactivity allowable for subobjects
        before they expire.
        """

    def getTimeoutMinutes():
        """
        Return the number of minutes allowed for subobject inactivity
        before expiration.
        """

    def getAddNotificationTarget():
        """
        Returns the currently registered 'add notification' value, or None.
        """

    def setAddNotificationTarget(f):
        """
        Cause the 'add notification' function to be 'f'.

        If 'f' is not callable and is a string, treat it as a physical
        path to a Zope Script object (Python Script, External Method,
        et. al).

        'add notify' functions need accept two arguments: 'item',
        which is the transient object being destroyed, and 'container',
        which is the transient object container which is performing
        the destruction.  For example::

          def addNotify(item, container):
              print "id of 'item' arg was %s" % item.getId()
        """

    def getDelNotificationTarget():
        """
        Returns the currently registered 'delete notification' value, or
        None.
        """

    def setDelNotificationTarget(f):
        """
        Cause the 'delete notification' function to be 'f'.

        If 'f' is not callable and is a string, treat it as a physical
        path to a Zope Script object (Python Script, External Method,
        et. al).

        'Before destruction' functions need accept two arguments: 'item',
        which is the transient object being destroyed, and 'container',
        which is the transient object container which is performing
        the destruction.  For example::

          def delNotify(item, container):
              print "id of 'item' arg was %s" % item.getId()
        """
