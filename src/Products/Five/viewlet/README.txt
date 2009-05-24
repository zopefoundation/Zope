=============================
Viewlets and Viewlet Managers
=============================

Let's start with some motivation. Using content providers allows us to insert
one piece of HTML content. In most Web development, however, you are often
interested in defining some sort of region and then allow developers to
register content for those regions.

  >>> from zope.viewlet import interfaces

Setup traversal stuff

  >>> import Products.Five
  >>> from Products.Five import zcml
  >>> zcml.load_config("configure.zcml", Products.Five)

Set a loose security policy because these are unit tests, security will be
tested in another file:

  >>> from AccessControl import SecurityManager
  >>> from Products.Five.viewlet.tests import UnitTestSecurityPolicy
  >>> from AccessControl.SecurityManagement import newSecurityManager
  >>> from AccessControl.SecurityManagement import noSecurityManager
  >>> noSecurityManager()
  >>> oldPolicy = SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())

Design Notes
------------

As mentioned above, besides inserting snippets of HTML at places, we more
frequently want to define a region in our page and allow specialized content
providers to be inserted based on configuration. Those specialized content
providers are known viewlets and are only available inside viewlet managers,
which are just a more complex example of content providers.

Unfortunately, the Java world does not implement this layer separately. The
viewlet manager is most similar to a Java "channel", but we decided against
using this name, since it is very generic and not very meaningful. The viewlet
has no Java counterpart, since Java does not implement content providers using
a component architecture and thus does not register content providers
specifically for viewlet managers, which I believe makes the Java
implementation less usefull as a generic concept. In fact, the main design
goal in the Java world is the implementation of reusable and sharable
portlets. The scope for Zope 3 is larger, since we want to provide a generic
framework for building pluggable user interfaces.


The Viewlet Manager
-------------------

In this implementation of viewlets, those regions are just content providers
called viewlet managers that manage a special type of content providers known
as viewlets. Every viewlet manager handles the viewlets registered for it:

  >>> from Products.Five.viewlet.tests import ILeftColumn

You can then create a viewlet manager using this interface now:

  >>> from Products.Five.viewlet import manager
  >>> LeftColumn = manager.ViewletManager('left', ILeftColumn)

Now we have to instantiate it in the context of an actual zope object:

  >>> import zope.interface
  >>> from OFS import SimpleItem, Folder
  >>> class Content(SimpleItem.SimpleItem):
  ...     zope.interface.implements(zope.interface.Interface)
  >>> obj_id = self.folder._setObject('content1', Content())
  >>> content = self.folder[obj_id]

  >>> from zope.publisher.browser import TestRequest
  >>> request = TestRequest()

  >>> from Products.Five.browser import BrowserView as View
  >>> view = View(content, request)

  >>> leftColumn = LeftColumn(content, request, view)

So initially nothing gets rendered:

  >>> leftColumn.update()
  >>> leftColumn.render()
  u''

But now we register some viewlets for the manager

  >>> import zope.component
  >>> from zope.publisher.interfaces.browser import IDefaultBrowserLayer
  >>> from zope.browser.interfaces import IBrowserView

  >>> class WeatherBox(object):
  ...     zope.interface.implements(interfaces.IViewlet)
  ...
  ...     def __init__(self, context, request, view, manager):
  ...         self.__parent__ = view
  ...         self.context = context
  ...
  ...     def update(self):
  ...         pass
  ...
  ...     def render(self):
  ...         return u'<div class="box">It is sunny today!</div>'

  >>> zope.component.provideAdapter(
  ...     WeatherBox,
  ...     (zope.interface.Interface, IDefaultBrowserLayer,
  ...     IBrowserView, ILeftColumn),
  ...     interfaces.IViewlet, name='weather')

  >>> class SportBox(object):
  ...     zope.interface.implements(interfaces.IViewlet)
  ...
  ...     def __init__(self, context, request, view, manager):
  ...         self.__parent__ = view
  ...         self.context = context
  ...
  ...     def update(self):
  ...         pass
  ...
  ...     def render(self):
  ...         return u'<div class="box">Patriots (23) : Steelers (7)</div>'

  >>> zope.component.provideAdapter(
  ...     SportBox,
  ...     (zope.interface.Interface, IDefaultBrowserLayer,
  ...      IBrowserView, ILeftColumn),
  ...     interfaces.IViewlet, name='sport')

and thus the left column is filled:

  >>> leftColumn.update()
  >>> print leftColumn.render()
  <div class="box">Patriots (23) : Steelers (7)</div>
  <div class="box">It is sunny today!</div>

But this is of course pretty lame, since there is no way of specifying how the
viewlets are put together. But we have a solution. The second argument of the
``ViewletManager()`` function is a template in which we can specify how the
viewlets are put together:

  >>> import os, tempfile
  >>> temp_dir = tempfile.mkdtemp()
  >>> leftColTemplate = os.path.join(temp_dir, 'leftCol.pt')
  >>> open(leftColTemplate, 'w').write('''
  ... <div class="left-column">
  ...   <tal:block repeat="viewlet options/viewlets"
  ...              replace="structure viewlet/render" />
  ... </div>
  ... ''')

  >>> LeftColumn = manager.ViewletManager('left', ILeftColumn,
  ...                                     template=leftColTemplate)
  >>> leftColumn = LeftColumn(content, request, view)

TODO: Fix this silly thing; viewlets should be directly available.

As you can see, the viewlet manager provides a global ``options/viewlets``
variable that is an iterable of all the avialable viewlets in the correct
order:

  >>> leftColumn.update()
  >>> print leftColumn.render().strip()
  <div class="left-column">
    <div class="box">Patriots (23) : Steelers (7)</div>
    <div class="box">It is sunny today!</div>
  </div>

You can also lookup the viewlets directly for management purposes:

  >>> leftColumn['weather']
  <WeatherBox ...>
  >>> leftColumn.get('weather')
  <WeatherBox ...>

If the viewlet is not found, then the expected behavior is provided:

  >>> leftColumn['stock']
  Traceback (most recent call last):
  ...
  ComponentLookupError: No provider with name `stock` found.

  >>> leftColumn.get('stock') is None
  True

Customizing the default Viewlet Manager
---------------------------------------

One important feature of any viewlet manager is to be able to filter and sort
the viewlets it is displaying. The default viewlet manager that we have been
using in the tests above, supports filtering by access availability and
sorting via the viewlet's ``__cmp__()`` method (default). You can easily
override this default policy by providing a base viewlet manager class.

In our case we will manage the viewlets using a global list:

  >>> shown = ['weather', 'sport']

The viewlet manager base class now uses this list:

  >>> class ListViewletManager(object):
  ...
  ...     def filter(self, viewlets):
  ...         viewlets = super(ListViewletManager, self).filter(viewlets)
  ...         return [(name, viewlet)
  ...                 for name, viewlet in viewlets
  ...                 if name in shown]
  ...
  ...     def sort(self, viewlets):
  ...         viewlets = dict(viewlets)
  ...         return [(name, viewlets[name]) for name in shown]

Let's now create a new viewlet manager:

  >>> LeftColumn = manager.ViewletManager(
  ...     'left', ILeftColumn, bases=(ListViewletManager,),
  ...     template=leftColTemplate)
  >>> leftColumn = LeftColumn(content, request, view)

So we get the weather box first and the sport box second:

  >>> leftColumn.update()
  >>> print leftColumn.render().strip()
  <div class="left-column">
    <div class="box">It is sunny today!</div>
    <div class="box">Patriots (23) : Steelers (7)</div>
  </div>

Now let's change the order...

  >>> shown.reverse()

and the order should switch as well:

  >>> leftColumn.update()
  >>> print leftColumn.render().strip()
  <div class="left-column">
    <div class="box">Patriots (23) : Steelers (7)</div>
    <div class="box">It is sunny today!</div>
  </div>

Of course, we also can remove a shown viewlet:

  >>> weather = shown.pop()
  >>> leftColumn.update()
  >>> print leftColumn.render().strip()
  <div class="left-column">
    <div class="box">Patriots (23) : Steelers (7)</div>
  </div>


Viewlet Base Classes
--------------------

To make the creation of viewlets simpler, a set of useful base classes and
helper functions are provided:

  >>> from Products.Five.viewlet import viewlet

The first class is a base class that simply defines the constructor:

  >>> base = viewlet.ViewletBase('context', 'request', 'view', 'manager')
  >>> base.context
  'context'
  >>> base.request
  'request'
  >>> base.__parent__
  'view'
  >>> base.manager
  'manager'

But a default ``render()`` method implementation is not provided:

  >>> base.render()
  Traceback (most recent call last):
  ...
  NotImplementedError: `render` method must be implemented by subclass.

If you have already an existing class that produces the HTML content in some
method, then the ``SimpleAttributeViewlet`` might be for you, since it can be
used to convert any class quickly into a viewlet:

  >>> class FooViewlet(viewlet.SimpleAttributeViewlet):
  ...     __page_attribute__ = 'foo'
  ...
  ...     def foo(self):
  ...         return 'output'

The `__page_attribute__` attribute provides the name of the function to call for
rendering.

  >>> foo = FooViewlet('context', 'request', 'view', 'manager')
  >>> foo.foo()
  'output'
  >>> foo.render()
  'output'

If you specify `render` as the attribute an error is raised to prevent
infinite recursion:

  >>> foo.__page_attribute__ = 'render'
  >>> foo.render()
  Traceback (most recent call last):
  ...
  AttributeError: render

The same is true if the specified attribute does not exist:

  >>> foo.__page_attribute__ = 'bar'
  >>> foo.render()
  Traceback (most recent call last):
  ...
  AttributeError: 'FooViewlet' object has no attribute 'bar'

To create simple template-based viewlets you can use the
``SimpleViewletClass()`` function. This function is very similar to its view
equivalent and is used by the ZCML directives to create viewlets. The result
of this function call will be a fully functional viewlet class. Let's start by
simply specifying a template only:

  >>> template = os.path.join(temp_dir, 'demoTemplate.pt')
  >>> open(template, 'w').write('''<div>contents</div>''')

  >>> Demo = viewlet.SimpleViewletClass(template)
  >>> print Demo(content, request, view, manager).render()
  <div>contents</div>

Now let's additionally specify a class that can provide additional features:

  >>> class MyViewlet(object):
  ...     myAttribute = 8

  >>> Demo = viewlet.SimpleViewletClass(template, bases=(MyViewlet,))
  >>> MyViewlet in Demo.__bases__
  True
  >>> Demo(content, request, view, manager).myAttribute
  8

The final important feature is the ability to pass in further attributes to
the class:

  >>> Demo = viewlet.SimpleViewletClass(
  ...     template, attributes={'here': 'now', 'lucky': 3})
  >>> demo = Demo(content, request, view, manager)
  >>> demo.here
  'now'
  >>> demo.lucky
  3

As for all views, they must provide a name that can also be passed to the
function:

  >>> Demo = viewlet.SimpleViewletClass(template, name='demoViewlet')
  >>> demo = Demo(content, request, view, manager)
  >>> demo.__name__
  'demoViewlet'

In addition to the the generic viewlet code above, the package comes with two
viewlet base classes and helper functions for inserting CSS and Javascript
links into HTML headers, since those two are so very common. I am only going
to demonstrate the helper functions here, since those demonstrations will
fully demonstrate the functionality of the base classes as well.

  >>> from zope.interface import Interface
  >>> from zope.component import getGlobalSiteManager
  >>> from zope.publisher.interfaces.browser import IDefaultBrowserLayer
  >>> def registerResource(name, factory):
  ...     gsm = getGlobalSiteManager()
  ...     gsm.registerAdapter(
  ...         factory,
  ...         required=(IDefaultBrowserLayer, ),
  ...         provided=Interface,
  ...         name=name,
  ...     )

The viewlet will look up the resource it was given and tries to produce the
absolute URL for it:

  >>> class JSResource(object):
  ...     def __init__(self, request):
  ...         self.request = request
  ...
  ...     def __call__(self):
  ...         return '/@@/resource.js'

  >>> registerResource('resource.js', JSResource)
  >>> JSViewlet = viewlet.JavaScriptViewlet('resource.js')
  >>> print JSViewlet(content, request, view, manager).render().strip()
  <script type="text/javascript" src="/@@/resource.js">
  </script>

The same works for the CSS resource viewlet:

  >>> class CSSResource(object):
  ...     def __init__(self, request):
  ...         self.request = request
  ...
  ...     def __call__(self):
  ...         return '/@@/resource.css'

  >>> registerResource('resource.css', CSSResource)

  >>> CSSViewlet = viewlet.CSSViewlet('resource.css')
  >>> print CSSViewlet(content, request, view, manager).render().strip()
  <link type="text/css" rel="stylesheet"
        href="/@@/resource.css" media="all" />

You can also change the media type and the rel attribute:

  >>> CSSViewlet = viewlet.CSSViewlet('resource.css', media='print', rel='css')
  >>> print CSSViewlet(content, request, view, manager).render().strip()
  <link type="text/css" rel="css" href="/@@/resource.css"
        media="print" />


A Complex Example
-----------------

The Data
~~~~~~~~

So far we have only demonstrated simple (maybe overly trivial) use cases of
the viewlet system. In the following example, we are going to develop a
generic contents view for files. The step is to create a file component:

  >>> class IFile(zope.interface.Interface):
  ...     data = zope.interface.Attribute('Data of file.')

  >>> class File(SimpleItem.SimpleItem):
  ...     zope.interface.implements(IFile)
  ...     def __init__(self, data=''):
  ...         self.__name__ = ''
  ...         self.data = data

Since we want to also provide the size of a file, here a simple implementation
of the ``ISized`` interface:

  >>> from zope import size
  >>> class FileSized(object):
  ...     zope.interface.implements(size.interfaces.ISized)
  ...     zope.component.adapts(IFile)
  ...
  ...     def __init__(self, file):
  ...         self.file = file
  ...
  ...     def sizeForSorting(self):
  ...         return 'byte', len(self.file.data)
  ...
  ...     def sizeForDisplay(self):
  ...         return '%i bytes' %len(self.file.data)

  >>> zope.component.provideAdapter(FileSized)

We also need a container to which we can add files:

  >>> class Container(Folder.Folder):
  ...     def __setitem__(self, name, value):
  ...         self._setObject(name, value)
  ...         value.__name__ = name

Here is some sample data:

  >>> container = Container()
  >>> obj_id = self.folder._setObject('container', container)
  >>> container = self.folder[obj_id]
  >>> container['mypage.html'] = File('<html><body>Hello World!</body></html>')
  >>> container['data.xml'] = File('<message>Hello World!</message>')
  >>> container['test.txt'] = File('Hello World!')


The View
~~~~~~~~

The contents view of the container should iterate through the container and
represent the files in a table:

  >>> contentsTemplate = os.path.join(temp_dir, 'contents.pt')
  >>> open(contentsTemplate, 'w').write('''
  ... <html>
  ...   <body>
  ...     <h1>Cotnents</h1>
  ...     <div tal:content="structure provider:contents" />
  ...   </body>
  ... </html>
  ... ''')

  >>> from Products.Five.browser.metaconfigure import makeClassForTemplate
  >>> Contents = makeClassForTemplate(contentsTemplate, name='contents.html')


The Viewlet Manager
~~~~~~~~~~~~~~~~~~~

Now we have to write our own viewlet manager. In this case we cannot use the
default implementation, since the viewlets will be looked up for each
different item:

  >>> shownColumns = []

  >>> class ContentsViewletManager(object):
  ...     zope.interface.implements(interfaces.IViewletManager)
  ...     index = None
  ...
  ...     def __init__(self, context, request, view):
  ...         self.context = context
  ...         self.request = request
  ...         self.__parent__ = view
  ...
  ...     def update(self):
  ...         rows = []
  ...         for name, value in self.context.objectItems():
  ...             rows.append(
  ...                 [zope.component.getMultiAdapter(
  ...                     (value, self.request, self.__parent__, self),
  ...                     interfaces.IViewlet, name=colname)
  ...                  for colname in shownColumns])
  ...             [entry.update() for entry in rows[-1]]
  ...         self.rows = rows
  ...
  ...     def render(self, *args, **kw):
  ...         return self.index(*args, **kw)

Now we need a template to produce the contents table:

  >>> tableTemplate = os.path.join(temp_dir, 'table.pt')
  >>> open(tableTemplate, 'w').write('''
  ... <table>
  ...   <tr tal:repeat="row view/rows">
  ...     <td tal:repeat="column row">
  ...       <tal:block replace="structure column/render" />
  ...     </td>
  ...   </tr>
  ... </table>
  ... ''')

From the two pieces above, we can generate the final viewlet manager class and
register it (it's a bit tedious, I know):

  >>> from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
  >>> ContentsViewletManager = type(
  ...     'ContentsViewletManager', (ContentsViewletManager,),
  ...     {'index': ZopeTwoPageTemplateFile('table.pt', temp_dir)})

  >>> zope.component.provideAdapter(
  ...     ContentsViewletManager,
  ...     (Container, IDefaultBrowserLayer, zope.interface.Interface),
  ...     interfaces.IViewletManager, name='contents')

Since we have not defined any viewlets yet, the table is totally empty:

  >>> contents = Contents(container, request)
  >>> print contents().strip()
  <html>
    <body>
      <h1>Cotnents</h1>
      <div>
        <table>
          <tr>
          </tr>
          <tr>
          </tr>
          <tr>
          </tr>
        </table>
      </div>
    </body>
  </html>


The Viewlets and the Final Result
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now let's create a first viewlet for the manager...

  >>> class NameViewlet(object):
  ...
  ...     def __init__(self, context, request, view, manager):
  ...         self.__parent__ = view
  ...         self.context = context
  ...
  ...     def update(self):
  ...         pass
  ...
  ...     def render(self):
  ...         return self.context.__name__

and register it:

  >>> zope.component.provideAdapter(
  ...     NameViewlet,
  ...     (IFile, IDefaultBrowserLayer,
  ...      zope.interface.Interface, interfaces.IViewletManager),
  ...     interfaces.IViewlet, name='name')

Note how you register the viewlet on ``IFile`` and not on the container. Now
we should be able to see the name for each file in the container:

  >>> print contents().strip()
  <html>
    <body>
      <h1>Cotnents</h1>
      <div>
        <table>
          <tr>
          </tr>
          <tr>
          </tr>
          <tr>
          </tr>
        </table>
      </div>
    </body>
  </html>

Waaa, nothing there! What happened? Well, we have to tell our user preferences
that we want to see the name as a column in the table:

  >>> shownColumns = ['name']
  >>> print contents().strip()
  <html>
    <body>
      <h1>Cotnents</h1>
      <div>
        <table>
          <tr>
            <td>
              mypage.html
            </td>
          </tr>
          <tr>
            <td>
              data.xml
            </td>
          </tr>
          <tr>
            <td>
              test.txt
            </td>
          </tr>
        </table>
      </div>
    </body>
  </html>

Let's now write a second viewlet that will display the size of the object for
us:

  >>> class SizeViewlet(object):
  ...
  ...     def __init__(self, context, request, view, manager):
  ...         self.__parent__ = view
  ...         self.context = context
  ...
  ...     def update(self):
  ...         pass
  ...
  ...     def render(self):
  ...         return size.interfaces.ISized(self.context).sizeForDisplay()

  >>> zope.component.provideAdapter(
  ...     SizeViewlet,
  ...     (IFile, IDefaultBrowserLayer,
  ...      zope.interface.Interface, interfaces.IViewletManager),
  ...     interfaces.IViewlet, name='size')

After we added it to the list of shown columns,

  >>> shownColumns = ['name', 'size']

we can see an entry for it:

  >>> print contents().strip()
  <html>
    <body>
      <h1>Cotnents</h1>
      <div>
        <table>
          <tr>
            <td>
              mypage.html
            </td>
            <td>
              38 bytes
            </td>
          </tr>
          <tr>
            <td>
              data.xml
            </td>
            <td>
              31 bytes
            </td>
          </tr>
          <tr>
            <td>
              test.txt
            </td>
            <td>
              12 bytes
            </td>
          </tr>
        </table>
      </div>
    </body>
  </html>

If we switch the two columns around,

  >>> shownColumns = ['size', 'name']

the result will be

  >>> print contents().strip()
  <html>
    <body>
      <h1>Cotnents</h1>
      <div>
        <table>
          <tr>
            <td>
              38 bytes
            </td>
            <td>
              mypage.html
            </td>
          </tr>
          <tr>
            <td>
              31 bytes
            </td>
            <td>
              data.xml
            </td>
          </tr>
          <tr>
            <td>
              12 bytes
            </td>
            <td>
              test.txt
            </td>
          </tr>
        </table>
      </div>
    </body>
  </html>


Supporting Sorting
~~~~~~~~~~~~~~~~~~

Oftentimes you also want to batch and sort the entries in a table. Since those
two features are not part of the view logic, they should be treated with
independent components. In this example, we are going to only implement
sorting using a simple utility:

  >>> class ISorter(zope.interface.Interface):
  ...
  ...     def sort(values):
  ...         """Sort the values."""

  >>> class SortByName(object):
  ...     zope.interface.implements(ISorter)
  ...
  ...     def sort(self, values):
  ...         return sorted(values, lambda x, y: cmp(x.__name__, y.__name__))

  >>> zope.component.provideUtility(SortByName(), name='name')

  >>> class SortBySize(object):
  ...     zope.interface.implements(ISorter)
  ...
  ...     def sort(self, values):
  ...         return sorted(
  ...             values,
  ...             lambda x, y: cmp(size.interfaces.ISized(x).sizeForSorting(),
  ...                              size.interfaces.ISized(y).sizeForSorting()))

  >>> zope.component.provideUtility(SortBySize(), name='size')

Note that we decided to give the sorter utilities the same name as the
corresponding viewlet. This convention will make our implementation of the
viewlet manager much simpler:

  >>> sortByColumn = ''

  >>> class SortedContentsViewletManager(manager.ViewletManagerBase):
  ...     zope.interface.implements(interfaces.IViewletManager)
  ...     index = None
  ...
  ...     def __init__(self, context, request, view):
  ...         self.context = context
  ...         self.request = request
  ...         self.__parent__ = view
  ...
  ...     def update(self):
  ...         values = self.context.objectValues()
  ...
  ...         if sortByColumn:
  ...            sorter = zope.component.queryUtility(ISorter, sortByColumn)
  ...            if sorter:
  ...                values = sorter.sort(values)
  ...
  ...         rows = []
  ...         for value in values:
  ...             rows.append(
  ...                 [zope.component.getMultiAdapter(
  ...                     (value, self.request, self.__parent__, self),
  ...                     interfaces.IViewlet, name=colname)
  ...                  for colname in shownColumns])
  ...             [entry.update() for entry in rows[-1]]
  ...         self.rows = rows
  ...
  ...     def render(self, *args, **kw):
  ...         return self.index(*args, **kw)

As you can see, the concern of sorting is cleanly separated from generating
the view code. In MVC terms that means that the controller (sort) is logically
separated from the view (viewlets). Let's now do the registration dance for
the new viewlet manager. We simply override the existing registration:

  >>> SortedContentsViewletManager = type(
  ...     'SortedContentsViewletManager', (SortedContentsViewletManager,),
  ...     {'index': ZopeTwoPageTemplateFile('table.pt', temp_dir)})

  >>> zope.component.provideAdapter(
  ...     SortedContentsViewletManager,
  ...     (Container, IDefaultBrowserLayer, zope.interface.Interface),
  ...     interfaces.IViewletManager, name='contents')

Finally we sort the contents by name:

  >>> shownColumns = ['name', 'size']
  >>> sortByColumn = 'name'

  >>> print contents().strip()
  <html>
    <body>
      <h1>Cotnents</h1>
      <div>
        <table>
          <tr>
            <td>
              data.xml
            </td>
            <td>
              31 bytes
            </td>
          </tr>
          <tr>
            <td>
              mypage.html
            </td>
            <td>
              38 bytes
            </td>
          </tr>
          <tr>
            <td>
              test.txt
            </td>
            <td>
              12 bytes
            </td>
          </tr>
        </table>
      </div>
    </body>
  </html>

Now let's sort by size:

  >>> sortByColumn = 'size'

  >>> print contents().strip()
  <html>
    <body>
      <h1>Cotnents</h1>
      <div>
        <table>
          <tr>
            <td>
              test.txt
            </td>
            <td>
              12 bytes
            </td>
          </tr>
          <tr>
            <td>
              data.xml
            </td>
            <td>
              31 bytes
            </td>
          </tr>
          <tr>
            <td>
              mypage.html
            </td>
            <td>
              38 bytes
            </td>
          </tr>
        </table>
      </div>
    </body>
  </html>

That's it! As you can see, in a few steps we have built a pretty flexible
contents view with selectable columns and sorting. However, there is a lot of
room for extending this example:

- Table Header: The table header cell for each column should be a different
  type of viewlet, but registered under the same name. The column header
  viewlet also adapts the container not the item. The header column should
  also be able to control the sorting.

- Batching: A simple implementation of batching should work very similar to
  the sorting feature. Of course, efficient implementations should somehow
  combine batching and sorting more effectively.

- Sorting in ascending and descending order: Currently, you can only sort from
  the smallest to the highest value; however, this limitation is almost
  superficial and can easily be removed by making the sorters a bit more
  flexible.

- Further Columns: For a real application, you would want to implement other
  columns, of course. You would also probably want some sort of fallback for
  the case that a viewlet is not found for a particular container item and
  column.


Cleanup
-------

  >>> ignore = SecurityManager.setSecurityPolicy(oldPolicy)
  >>> import shutil
  >>> shutil.rmtree(temp_dir)
