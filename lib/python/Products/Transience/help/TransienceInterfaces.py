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

"""

class TransientObjectContainer:
    """
    TransientObjectContainers hold transient objects, most often,
    session data.

    You will rarely have to script a transient object
    container. You'll almost always deal with a TransientObject
    itself which you'll usually get as 'REQUEST.SESSION'.
    """
    
    def getId(self):
        """
        Returns a meaningful unique id for the object.

        Permission -- Always available
        """

    def get(self, k, default=None):
        """
        Return value associated with key k.  If value associated with k does
        not exist, return default.

        Permission -- 'Access Transient Objects'
        """

    def has_key(self, k):
        """
        Return true if container has value associated with key k, else
        return false.

        Permission -- 'Access Transient Objects'
        """

    def new(self, k):
        """
        Creates a new subobject of the type supported by this container
        with key "k" and returns it.

        If an object already exists in the container with key "k", a
        KeyError is raised.

        "k" must be a string, else a TypeError is raised.

        If the container is 'full', a MaxTransientObjectsExceeded will
        be raised.

        Permission -- 'Create Transient Objects'
        """

    def new_or_existing(self, k):
        """
        If an object already exists in the container with key "k", it
        is returned.

        Otherwiser, create a new subobject of the type supported by this
        container with key "k" and return it.

        "k" must be a string, else a TypeError is raised.

        If the container is 'full', a MaxTransientObjectsExceeded exception
        be raised.

        Permission -- 'Create Transient Objects'
        """
    
    def setTimeoutMinutes(self, timeout_mins):
        """
        Set the number of minutes of inactivity allowable for subobjects
        before they expire.

        Permission -- 'Manage Transient Object Container'
        """

    def getTimeoutMinutes(self):
        """
        Return the number of minutes allowed for subobject inactivity
        before expiration.

        Permission -- 'View management screens'
        """

    def getAddNotificationTarget(self):
        """
        Returns the current 'after add' function, or None.

        Permission -- 'View management screens'
        """

    def setAddNotificationTarget(self, f):
        """
        Cause the 'after add' function to be 'f'.

        If 'f' is not callable and is a string, treat it as a Zope path to
        a callable function.

        'after add' functions need accept a single argument: 'item', which
        is the item being added to the container.

        Permission -- 'Manage Transient Object Container'
        """

    def getDelNotificationTarget(self):
        """
        Returns the current 'before destruction' function, or None.

        Permission -- 'View management screens'
        """

    def setDelNotificationTarget(self, f):
        """
        Cause the 'before destruction' function to be 'f'.

        If 'f' is not callable and is a string, treat it as a Zope path to
        a callable function.

        'before destruction' functions need accept a single argument: 'item',
        which is the item being destroyed.

        Permission -- 'Manage Transient Object Container'
        """


class TransientObject:
    """
    A transient object is a temporary object contained in a transient
    object container.

    Most of the time you'll simply treat a transient object as a
    dictionary. You can use Python sub-item notation::

      SESSION['foo']=1
      foo=SESSION['foo']
      del SESSION['foo']

    When using a transient object from Python-based Scripts or DTML
    you can use the 'get', 'set', and 'delete' methods instead.

    Methods of transient objects are not protected by security
    assertions.

    It's necessary to reassign mutuable sub-items when you change
    them. For example::

      l=SESSION['myList']
      l.append('spam')
      SESSION['myList']=l

    This is necessary in order to save your changes.  Note that this caveat
    is true even for mutable subitems which inherit from the
    Persistence.Persistent class.
    """

    def getId(self):
        """
        Returns a meaningful unique id for the object.

        Permission -- Always available
        """

    def getContainerKey(self):
        """
        Returns the key under which the object is "filed" in its container.
        getContainerKey will often return a differnt value than the value
        returned by getId.

        Permission -- Always available
        """
        
    def invalidate(self):
        """
        Invalidate (expire) the transient object.

        Causes the transient object container's "before destruct" method
        related to this object to be called as a side effect.

        Permission -- Always available
        """

    def getLastAccessed(self):
        """
        Return the time the transient object was last accessed in
        integer seconds-since-the-epoch form.

        Permission -- Always available
        """

    def setLastAccessed(self):
        """
        Cause the last accessed time to be set to now.

        Permission -- Always available
        """

    def getCreated(self):
        """
        Return the time the transient object was created in integer
        seconds-since-the-epoch form.

        Permission -- Always available
        """

    def keys(self):
        """
        Return sequence of key elements.

        Permission -- Always available
        """

    def values(self):
        """
        Return sequence of value elements.

        Permission -- Always available
        """

    def items(self):
        """
        Return sequence of (key, value) elements.

        Permission -- Always available
        """

    def get(self, k, default='marker'):
        """
        Return value associated with key k.  If k does not exist and default
        is not marker, return default, else raise KeyError.

        Permission -- Always available
        """

    def has_key(self, k):
        """
        Return true if item referenced by key k exists.

        Permission -- Always available
        """

    def clear(self):
        """
        Remove all key/value pairs.

        Permission -- Always available
        """

    def update(self, d):
        """
        Merge dictionary d into ourselves.

        Permission -- Always available
        """

    def set(self, k, v):
        """
        Call __setitem__ with key k, value v.

        Permission -- Always available
        """

    def delete(self, k):
        """
        Call __delitem__ with key k.

        Permission -- Always available
        """

class MaxTransientObjectsExceeded:
    """
    An exception importable from the Products.Transience.Transience module
    which is raised when an attempt is made to add an item to a
    TransientObjectContainer that is 'full'.

    This exception may be caught in PythonScripts through a normal import.
    A successful import of the exception can be achieved via::

      from Products.Transience import MaxTransientObjectsExceeded
    """


