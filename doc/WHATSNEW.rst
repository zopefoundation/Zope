What's new in Zope 2.12
=======================

The article explains the new high-level features and changes found in this
version of Zope 2.

You can have a look at the `detailed change log <CHANGES.html>`_ to learn
about all minor new features and bugs being solved in this release.


Support for newer Python versions
---------------------------------

Zope 2 has supported and required Python 2.4 since its 2.9 release in summer
2006. Later versions of Python have so far been unsupported by Zope 2.

This version of Zope 2 adds support for Python 2.6 instead. As neither Python
2.4 nor Python 2.5 are officially maintained any longer. Python 2.4 on 64-bit
platforms is known to be incompatible with Zope 2.12. On 32-bit it could work
at your own risk. While there are no known incompatibilities with Python 2.5
it is not recommended.

Python 3 is a backwards incompatible release of Python and not supported. At
this point there is no concrete roadmap for adoption of Python 3. It is
expected to be a question of multiple major Zope 2 releases or years, though.


Fully eggified
--------------

Zope 2 itself is now fully eggified and compatible with `setuptools
<http://pypi.python.org/pypi/setuptools>`_. You can use popular tools like
`easy_install <http://peak.telecommunity.com/DevCenter/EasyInstall>`_ or
`zc.buildout <http://pypi.python.org/pypi/zc.buildout>`_ to install Zope 2.

Releases of Zope 2 can be found at and will be installable from the Python
package index at http://pypi.python.org/pypi/Zope2.

The repackaging of Zope 2 into an eggified form and accompanying changes to the
file system layout have caused a number of changes. The environment variables
`SOFTWARE_HOME` and `ZOPE_HOME` are no longer available nor set in the control
scripts. If you need to access data files inside the Zope 2 package, you can
for example use `import os, OFS; os.path.dirname(OFS.__file__)` to locate the
files inside the OFS package.

In general it is discouraged to rely on the `lib/python` and `Products`
directories to make code available to the running Zope process. While these
mechanisms continue to work, you are encouraged to use normal distutils or
setuptools managed packages and add these to your `sys.path` using any of the
standard Python mechanisms. To create isolated Python environments both
`zc.buildout <http://pypi.python.org/pypi/zc.buildout>`_ and `virtualenv
<http://pypi.python.org/pypi/virtualenv>`_ are in wide-spread use.


Zope 3
------

This version of Zope 2 does no longer includes a full version of the Zope 3
application server nor a specific release of it. Instead it includes a minimal
set of packages from the former Zope 3 project. Only those packages actually
used by Zope 2 itself are still included. Examples of such packages include
zope.interface, zope.component, zope.i18n, zope.tal and many more.

Zope 2.12 marks a transitionary release, where a number of zope.app packages
are still included. An ongoing effort to refactor those packages into more
reusable and minimal packages is going on and will result in no zope.app
packages being used or shipped with anymore as part of Zope 2. Zope 2.13 does
no longer ship with any zope.app packages.

If you are using zope.app packages inside your own codebase, you should make
sure to declare these as dependencies of your packages or otherwise follow the
refactoring effort and remove your dependency on these packages.

As a result of this refocussing on more minimal dependencies, the number of
packages included by Zope 2 could be dramatically reduced from about 120
additional packages to just over 70. The total code size of Zope 2 and its
dependencies has decreased by over 200,000 lines of code as a result.


ZODB 3.9
--------

This version of Zope 2 includes the latest version of the `ZODB (3.9)
<http://pypi.python.org/pypi/ZODB3>`_. It has a multitude of new configuration
options and bug fixes. File storages have gotten native support for blob
storages and demo storages have been expanded extensively. There is a large
number of options to tune ZEO servers and clients in large scale environments
and control cache invalidation and packaging to a much wider degree.

You can read more about the detailed changes in the `ZODB3 change log
<http://pypi.python.org/pypi/ZODB3>`_ for version 3.9.


Module cleanup
--------------

As with every release of Zope 2 this version has removed various modules
which have been deprecated in prior versions.

Most notably ZClasses and supporting modules have been removed entirely from
Zope 2. As a result the persistent product registry has been made optional, but
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

Zope 2 now uses `Sphinx <http://sphinx.pocoo.org/>`_ to create pleasant HTML
representations of its documentation. An effort is underway to update the
publicly available documentation using Sphinx at http://docs.zope.org/.

So far the Zope 2 Book, the Zope Developers Guide and many smaller articles
have been converted to reStructuredText and their content updated.


Acquisition redux
-----------------

The short technical version of this change is: "Acquisition has been made aware
of __parent__ pointers". What sounds like a small change is actually a major
step in the integration story for Zope components based technology into Zope 2.

While integrating the Zope component architecture and its many concepts into
Zope 2 an integration layer called Five (Zope 2 + 3) has been created. One of
the major reasons for the necessity of an integration layer has been in the way
Zope 2 was tightly coupled to the concept of Acquisition. The entire security
machinery, object traversal and publication has been relying on this.

All classes, which wanted to interact with Zope 2 in any non-trivial way, had
to inherit from the Acquisition base classes. As a result almost no external
package could directly work inside Zope 2 but required an integration layer.

With this version of Zope 2, objects have a new option of providing location
awareness to Zope APIs. This new option is to provide an explicit parent
pointer in the ``__parent__`` attribute, much like specified by the ILocation
API from `zope.location <http://pypi.python.org/pypi/zope.location>`_. Browser
views and other location-dependent components implement ILocation already.

Classes adhering to this convention need to get `__parent__` pointers set to
their container object, when being put into the container. Code that operates
on such objects can then walk up the containment hierarchy by following the
pointers. In Acquisition based classes no information would be stored on the
objects, but Acquisition wrappers are constructed around the objects instead.
Only those wrappers would hold the container references. The Acquisition
wrapping relies on the objects to provide an `__of__` method as done by the
Acquisition base classes.

The most common way of getting the container of an instance is to call::

  from Acquisition import aq_parent
  
  container = aq_parent(instance)

For instances providing the ILocation interface the common way is::

  container = instance.__parent__

There are various `aq_*` methods available for various other tasks related to
locating objects in the containment hierarchy. So far virtually all objects in
Zope 2 would participate in Acquisition. As a side-effect many people relied on
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
available as attributes. While all code inside Zope 2 itself still supports
this, it does no longer rely on those but makes proper use of the functions
provided by the Acquisition package.

To understand the interaction between the new and old approach here is a
little example::

  >>> class Location(object):
  ...     def __init__(self, name):
  ...         self.__name__ = name
  ...     def __repr__(self):
  ...         return self.__name__

  # Create an Acquisition variant of the class:

  >>> import Acquisition
  >>> class Implicit(Location, Acquisition.Implicit):
  ...     pass

  # Create two implicit instances:

  >>> root = Implicit('root')
  >>> folder = Implicit('folder')

  # And two new Acquisition-free instances:

  >>> container = Location('container')
  >>> item = Location('item')

  # Provide the containment hints:

  >>> folder = folder.__of__(root)
  >>> container.__parent__ = folder
  >>> item.__parent__ = container

  # Test the containtment chain:

  >>> from Acquisition import aq_parent
  >>> aq_parent(container)
  folder

  >>> from Acquisition import aq_chain
  >>> aq_chain(item)
  [item, container, folder, root]

  # Explicit pointers take precedence over Acquisition wrappers:

  >>> item2 = Implicit('item2')
  >>> item2 = item2.__of__(folder)
  >>> item2.__parent__ = container

  >>> aq_chain(item2)
  [item2, container, folder, root]

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
more reusable outside of Zope 2, this should be of tremendous help.


Object managers and IContainer
------------------------------

One of the fundamental parts of Zope 2 is the object file system as implemented
in the `OFS` package. A central part of this package is an underlying class
called `ObjectManager`. It is a base class of the standard `Folder` used
for many container-ish classes inside Zope 2.

The API to access objects in an object manager or to add objects to one has
been written many years ago. Since those times Python itself has gotten
standard ways to access objects in containers and work with them. Those Python
API's are most familiar to most developers working with Zope. The Zope
components libraries have formalized those API's into the general IContainer
interface in the zope.container package. In this version of Zope 2 the standard
OFS ObjectManager fully implements this IContainer interface in addition to its
old API.

 >>> from zope.container.interfaces import IContainer
 >>> from OFS.ObjectManager import ObjectManager
 >>> IContainer.implementedBy(ObjectManager)
 True

You can now write your code in a way that no longer ties it to object managers
alone, but can support any class implementing IContainer instead. In
conjunction with the Acquisition changes above, this will increase your chances
of being able to reuse existing packages not specifically written for Zope 2 in
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

