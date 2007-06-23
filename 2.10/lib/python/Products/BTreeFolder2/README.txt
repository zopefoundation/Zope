
Contact
=======

Shane Hathaway
Zope Corporation
shane at zope dot com


BTreeFolder2 Product
====================

BTreeFolder2 is a Zope product that acts like a Zope folder but can
store many more items.

When you fill a Zope folder with too many items, both Zope and your
browser get overwhelmed.  Zope has to load and store a large folder
object, and the browser has to render large HTML tables repeatedly.
Zope can store a lot of objects, but it has trouble storing a lot of
objects in a single standard folder.

Zope Corporation once had an extensive discussion on the subject.  It
was decided that we would expand standard folders to handle large
numbers of objects gracefully.  Unfortunately, Zope folders are used
and extended in so many ways today that it would be difficult to
modify standard folders in a way that would be compatible with all
Zope products.

So the BTreeFolder product was born.  It stored all subobjects in a
ZODB BTree, a structure designed to allow many items without loading
them all into memory.  It also rendered the contents of the folder as
a simple select list rather than a table.  Most browsers have no
trouble rendering large select lists.

But there was still one issue remaining.  BTreeFolders still stored
the ID of all subobjects in a single database record.  If you put tens
of thousands of items in a single BTreeFolder, you would still be
loading and storing a multi-megabyte folder object.  Zope can do this,
but not quickly, and not without bloating the database.

BTreeFolder2 solves this issue.  It stores not only the subobjects but
also the IDs of the subobjects in a BTree.  It also batches the list
of items in the UI, showing only 1000 items at a time.  So if you
write your application carefully, you can use a BTreeFolder2 to store
as many items as will fit in physical storage.

There are products that depend on the internal structure of the
original BTreeFolder, however.  So rather than risk breaking those
products, the product has been renamed.  You can have both products
installed at the same time.  If you're developing new applications,
you should use BTreeFolder2.


Installation
============

Untar BTreeFolder2 in your Products directory and restart Zope.
BTreeFolder2 will now be available in your "Add" drop-down.

Additionally, if you have CMF installed, the BTreeFolder2 product also
provides the "CMF BTree Folder" addable type.


Usage
=====

The BTreeFolder2 user interface shows a list of items rather than a
series of checkboxes.  To visit an item, select it in the list and
click the "edit" button.

BTreeFolder2 objects provide Python dictionary-like methods to make them
easier to use in Python code than standard folders::

    has_key(key)
    keys()
    values()
    items()
    get(key, default=None)
    __len__()

keys(), values(), and items() return sequences, but not necessarily
tuples or lists.  Use len(folder) to call the __len__() method.  The
objects returned by values() and items() have acquisition wrappers.

BTreeFolder2 also provides a method for generating unique,
non-overlapping IDs::

    generateId(prefix='item', suffix='', rand_ceiling=999999999)

The ID returned by this method is guaranteed to not clash with any
other ID in the folder.  Use the returned value as the ID for new
objects.  The generated IDs tend to be sequential so that objects that
are likely related in some way get loaded together.

BTreeFolder2 implements the full Folder interface, with the exception
that the superValues() method does not return any items.  To implement
the method in the way the Zope codebase expects would undermine the
performance benefits gained by using BTreeFolder2.


Repairing BTree Damage
======================

Certain ZODB bugs in the past have caused minor corruption in BTrees.
Fortunately, the damage is apparently easy to repair.  As of version
1.0, BTreeFolder2 provides a 'manage_cleanup' method that will check
the internal structure of existing BTreeFolder2 instances and repair
them if necessary.  Many thanks to Tim Peters, who fixed the BTrees
code and provided a function for checking a BTree.

Visit a BTreeFolder2 instance through the web as a manager.  Add
"manage_cleanup" to the end of the URL and request that URL.  It may
take some time to load and fix the entire structure.  If problems are
detected, information will be added to the event log.


Future
======

BTreeFolder2 will be maintained for Zope 2.  Zope 3, however, is not
likely to require BTreeFolder, since the intention is to make Zope 3
folders gracefully expand to support many items.


