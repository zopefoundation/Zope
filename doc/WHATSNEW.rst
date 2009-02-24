What's new in Zope 2.12
=======================

The article explains the new high-level features and changes found in this
version of Zope2.

You can have a look at the `detailed change log <CHANGES.html>`_ to learn
about all minor new features and bugs being solved in this release.


Support for newer Python versions
---------------------------------

Zope2 has supported and required Python 2.4 since its 2.9 release in
summer 2006. Later versions of Python have so far been incompatible with
Zope2.

This version of Zope2 adds support for both Python 2.5 and 2.6 at the same
time. As Python 2.4 is no longer maintained itself, it is no longer officially
supported by this Zope2 version. There is however no code in Zope2 yet which
requires Python 2.5, so applications built on top of Zope2 should still
continue to run with Python 2.4.

Python 3 is a backwards incompatible release of Python and not supported. At
this point there is no concrete roadmap for adoption of Python 3. It is
expected to be a question of multiple major Zope2 releases or years, though.


Fully eggified
--------------

Zope2 itself is now fully eggified and compatible with `setuptools
<http://pypi.python.org/pypi/setuptools>`_. You can use popular tools like
`easy_install <http://peak.telecommunity.com/DevCenter/EasyInstall>`_ or
`zc.buildout <http://pypi.python.org/pypi/zc.buildout>`_ to install Zope2.

Releases of Zope2 can be found at and will be installable from the Python
package index at http://pypi.python.org/pypi/Zope2.

The repackaging of Zope2 into an eggified form and accompanying changes to the
file system layout have caused a number of changes. The environment variables
`SOFTWARE_HOME` and `ZOPE_HOME` are no longer available nor set in the control
scripts. If you need to access data files inside the Zope2 package, you can for
example use `import os, OFS; os.path.dirname(OFS.__file__)` to locate the files
inside the OFS package.

In general it is discouraged to rely on the `lib/python` and `Products`
directories to make code available to the running Zope process. While these
mechanisms continue to work, you are encouraged to use normal distutils or
setuptools managed packages and add these to your `sys.path` using any of the
standard Python mechanisms. To create isolated Python environments both
`zc.buildout <http://pypi.python.org/pypi/zc.buildout>`_ and `virtualenv
<http://pypi.python.org/pypi/virtualenv>`_ are in wide-spread use.


Latest version of Zope Components
---------------------------------

This version of Zope2 is compatible with and is based on Zope 3.5.

A major focus of the new version of the Zope component libraries was to
refactor package dependencies to generate more maintainable and better
structured code. Based on this effort the number of packages included by
Zope2 could be dramatically reduced from about 120 additional packages to
just over 60. The total code size of Zope2 and its dependencies has decreased
by over 200,000 lines of code as a result.

You can find more information about the changes in Zope 3.5 at
http://download.zope.org/zope3.5/. Upgrade information from Zope 3.4 to 3.5
can be found at http://docs.zope.org/zope3docs/migration/34to35.html.


ZODB 3.9
--------

This version of Zope2 includes the latest version of the `ZODB (3.9)
<http://pypi.python.org/pypi/ZODB3>`_. It has a multitude of new configuration
options and bug fixes. File storages have gotten native support for blob
storages and demo storages have been expanded extensively. There is a large
number of options to tune ZEO servers and clients in large scale environments
and control cache invalidation and packaging to a much wider degree.

You can read more about the detailed changes in the `ZODB3 change log
<http://pypi.python.org/pypi/ZODB3>`_ for version 3.9.


Module cleanup
--------------

As with every release of Zope2 this version has removed various modules
which have been deprecated in prior versions.

Most notably ZClasses and supporting modules have been removed entirely from
Zope2. As a result the persistent product registry has been made optional, but
is still enabled by default. If your application does not rely on the registry,
you can now disable it by specifying::

  enable-product-installation off

inside your `zope.conf` file. With the option turned off Zope will no longer
write any new transactions to your database during startup in most cases.

With the upgrade to ZODB 3.9 database-level version support is no longer
available. Many of the modules in `Products.OFSP` have been removed as a
result. The low level API to load objects from the database has lost its
version argument as a result of this.


Documentation updates
---------------------

Zope2 now uses `Sphinx <http://sphinx.pocoo.org/>`_ to create pleasant HTML
representations of its documentation. An effort is underway to update the
publicly available documentation using Sphinx at http://docs.zope.org/.

So far the Zope2 Book, the Zope Developers Guide and many smaller articles
have been converted to reStructuredText and their content updated.


Acquisition redux
-----------------

The short technical version of this change is: "Acquisition has been made aware
of __parent__ pointers". What sounds like a small change is actually a major
step in the integration story for Zope components based technology into Zope2.

While integrating the Zope component architecture and its many concepts into
Zope2 an integration layer called Five (Zope 2 + 3) has been created. One of
the major reasons for the necessity of an integration layer has been in the way
Zope2 was tightly coupled to the concept of Acquisition. The entire security
machinery, object traversal and publication has been relying on this.

All classes, which wanted to interact with Zope2 in any non-trivial way, had to
inherit from the Acquisition base classes. As a result almost no external
package could directly work inside Zope2 but required an integration layer.

With this version of Zope2 classes do have a second option of providing
location awareness to Zope API's in a transparent way. The second option is the
`zope.location <http://pypi.python.org/pypi/zope.location>`_ API as described
by the ILocation interface.

Classes implementing this interface get `__parent__` pointers set to their
container object, when being put into the container. Code that operates on such
objects can then walk up the containment hierarchy by following the pointers.
In Acquisition based classes no information would be stored on the objects, but
Acquisition wrappers are constructed around the objects instead. Only those
wrappers would hold the container references. The Acquisition wrapping relies
on the objects to provide an `__of__` method as done by the Acquisition base
classes.

The standard way of getting the container of an instance is to call::

  from Acquisition import aq_parent
  
  container = aq_parent(instance)

There are various `aq_*` methods available for various other tasks related to
locating objects in the containment hierarchy. So far virtually all objects in
Zope2 would participate in Acquisition. As a side-effect many people relied on
Acquisition wrappers to be found around their objects. This caused code to rely
on accessing the `aq_*` methods as attributes of the wrapper::

  container = instance.aq_parent

While all the existing API's still work as before, Acquisition now respects
`__parent__` pointers to find the container for an object. It will also not
unconditionally try to call the `__of__` method of objects anymore, but protect
it with a proper interface check::

  from Acquisition.interfaces import IAcquirer

  if IAcquirer.providedBy(instance):
      instance = instance.__of__(container)

In addition to this check you should no longer rely on the `aq_*` methods to be
available as attributes. While all code inside Zope2 itself still supports
this, it does no longer rely on thosem but makes proper use of the functions
provided by the Acquisition package.

To understand the interaction between the new and old approach here is a
little example::

  >>> class O(object):
  ...     def __init__(self, name):
  ...         self.__name__ = str(name)
  ...     def __repr__(self):
  ...         return self.__class__.__name__ + self.__name__

  # Create an Acquisition variant of the class:

  >>> from Acquisition import Implicit
  >>> class I(O, Implicit):
  ...     pass

  >>> i1 = I(1)
  >>> i2 = I(2)
  >>> o1 = O(1)
  >>> o2 = O(2)

  # Provide the containment hints:

  >>> i2 = i2.__of__(i1)
  >>> o1.__parent__ = i2
  >>> o2.__parent__ = o1

  # Test the containtment chain:

  >>> from Acquisition import aq_parent
  >>> aq_parent(o1)
  I2

  >>> from Acquisition import aq_chain
  >>> aq_chain(o2)
  [O2, O1, I2, I1]

  # Explicit pointers take precedence over Acquisition wrappers:

  >>> i3 = I(3)
  >>> i3 = i3.__of__(i2)
  >>> i3.__parent__ = o1

  >>> aq_chain(i3)
  [I3, O1, I2, I1]

For a less abstract example, you so far had to do::

  >>> from Acquisition import aq_inner
  >>> from Acquisition import aq_parent
  >>> from Products import Five

  >>> class MyView(Five.browser.BrowserView):
  ...
  ...     def do_something(self):
  ...         container = aq_parent(aq_inner(self.context))

Instead you can now do::

  >>> import zope.publisher.browser

  >>> class MyView(zope.publisher.browser.BrowserView):
  ...
  ...     def do_something(self):
  ...         container = aq_parent(self.context)

As the zope.publisher BrowserView supports the ILocation interface, all of this
works automatically. A view considers its context as its parent as before, but
no longer needs Acquisition wrapping for the Acquisition machinery to
understand this. The next time you want to use a package or make your own code
more reusable outside of Zope2, this should be of tremendous help.


Object managers and IContainer
------------------------------

One of the fundamental parts of Zope2 is the object file system as implemented
in the `OFS` package. A central part of this package is an underlying class
called `ObjectManager`. It is a base class of the standard `Folder` used
for many container-ish classes inside Zope2.

The API to access objects in an object manager or to add objects to one has
been written many years ago. Since those times Python itself has gotten
standard ways to access objects in containers and work with them. Those Python
API's are most familiar to most developers working with Zope. The Zope
components libraries have formalized those API's into the general IContainer
interface in the zope.container package. In this version of Zope2 the standard
OFS ObjectManager fully implements this IContainer interface in addition to its
old API.

 >>> from zope.container.interfaces import IContainer
 >>> from OFS.ObjectManager import ObjectManager
 >>> IContainer.implementedBy(ObjectManager)
 True

You can now write your code in a way that no longer ties it to object managers
alone, but can support any class implementing IContainer instead. In
conjunction with the Acquisition changes above, this will increase your chances
of being able to reuse existing packages not specifically written for Zope2 in
a major way.

Here's an example of how you did work with object managers before::

  >>> from OFS.Folder import Folder
  >>> from OFS.SimpleItem import SimpleItem

  >>> folder = Folder('folder')
  >>> item1 = SimpleItem('item1')
  >>> item2 = SimpleItem('item2')

  >>> result = folder._setObject('item1', item1)
  >>> result = folder._setObject('item2', item2)

  >>> folder.objectIds()
  ['item1', 'item2']

  >>> folder.objectValues()
  [<SimpleItem at folder/>, <SimpleItem at folder/>]

  >>> if folder.hasObject('item2')
  ...     folder._delObject('item2')

Instead of this special API, you can now use::

  >>> from OFS.Folder import Folder
  >>> from OFS.SimpleItem import SimpleItem

  >>> folder = Folder('folder')
  >>> item1 = SimpleItem('item1')
  >>> item2 = SimpleItem('item2')

  >>> folder['item1'] = item1
  >>> folder['item2'] = item2

  >>> folder.keys()
  ['item1', 'item2']

  >>> folder.values()
  [<SimpleItem at folder/>, <SimpleItem at folder/>]

  >>> folder.get('item1')
  <SimpleItem at folder/>

  >>> if 'item2' in folder:
  ...     del folder['item2']

  >>> folder.items()
  [('item1', <SimpleItem at folder/>)]

