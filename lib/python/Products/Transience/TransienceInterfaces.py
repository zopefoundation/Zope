########################################################################## 
#
# Zope Public License (ZPL) Version 1.1
# -------------------------------------
# 
# Copyright (c) Zope Corporation.  All rights reserved.
# 
# This license has been certified as open source.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Zope Corporation 
#      for use in the Z Object Publishing Environment
#      (http://www.zope.com/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 4. Names associated with Zope or Zope Corporation must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Zope Corporation.
# 
# 5. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Zope Corporation
#      for use in the Z Object Publishing Environment
#      (http://www.zope.com/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 6. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY ZOPE CORPORATION ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL ZOPE CORPORATION OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Zope Corporation and
# many individuals on behalf of Zope Corporation.  Specific
# attributions are listed in the accompanying credits file.
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

import Interface

class Transient(Interface.Base):
    def invalidate(self):
        """
        Invalidate (expire) the transient object.

        Causes the transient object container's "before destruct" method
        related to this object to be called as a side effect.
        """

    def isValid(self):
        """
        Return true if transient object is still valid, false if not.
        A transient object is valid if its invalidate method has not been
        called.
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
        Returns a meaningful unique id for the object.  Note that this id
        need not the key under which the object is stored in its container.
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
        objects obtained via __getitem__, even if they support the ZODB
        Persistence interface.  In order to ensure that changes to mutable
        values are persisted, you need to explicitly put the value back in
        to the mapping via __setitem__.
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
    def get(self, k, default=None):
        """
        Return value associated with key k via __getitem__.  If value
        associated with k does not exist, return default.
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
    def new(self, k, wrap_with=None):
        """
        Creates a new subobject of the type supported by this container
        with key "k" and returns it.

        If an object already exists in the container with key "k", a
        KeyError is raised.

        If wrap_with is non-None, the subobject is returned in the
        acquisition context of wrap_in, else it is returned in
        the acquisition context of this transient object container.

        "k" must be a string, else a TypeError is raised.
        """

    def new_or_existing(self, k, wrap_with=None):
        """
        If an object already exists in the container with key "k", it
        is returned.

        Otherwise, create a new subobject of the type supported by this
        container with key "k" and return it.

        If wrap_with is non-None, the subobject is returned in the
        acquisition context of wrap_in, else it is returned in
        the acquisition context of this transient object container.

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
        Returns the currently registered 'add notification' value, or None.
        """

    def setAddNotificationTarget(self, f):
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

    def getDelNotificationTarget(self):
        """
        Returns the currently registered 'delete notification' value, or
        None.
        """

    def setDelNotificationTarget(self, f):
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
