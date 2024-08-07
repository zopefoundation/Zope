What's new in Zope
==================
The article explains the new high-level features and changes found in Zope.

You can have a look at the `detailed change log <./changes.html>`_ to learn
about all minor new features and bugs being solved in the latest release.

The `Zope release schedule <https://www.zope.dev/releases.html>`_
on `www.zope.dev <https://www.zope.dev>`_ explains which versions are
supported and for how long.

.. attention::

    If you are upgrading from Zope 2, make sure you study the
    :ref:`zope4migration` documentation


What's new in Zope 5
--------------------

Added support for Python 3.9
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Python 3.9 is now fully supported by Zope 5.

* Zope 5.4 and newer also supports Python 3.10.

* Zope 5.7 and newer also supports Python 3.11.

Dropped support for Python 2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Zope 5 supports Python 3 only, versions 3.6 up through 3.11. All support code
and special casing for Python 2, including the use of the ``six`` package, have
been removed.

Dropped support for ``ZServer``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
As ``ZServer`` only supports Python 2, its integration has been removed. Only
`WSGI` is now supported for web service.



What's new in Zope 4
--------------------

Restored sane version numbering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Version numbers for Zope have been confusing in the past. The original Zope
project iterated through version one to two up to version 2.13. In parallel
a separate project was launched using the name Zope 3. Zope 3 wasn't a new
version of the original Zope project and in hindsight should have used a
different project name. These days this effort is known as BlueBream.

In order to avoid confusion between the separate Zope 3 project and a
new version of this project, it was decided to skip ahead and use
Zope 4.0 as the next version number. The increase in the major part of
the version also indicates the number of backwards incompatible changes
found in this release.


Extended Python version support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Zope 4 supports Python 2.7 and Python 3 versions 3.5 up to 3.8.

The Python 3 support currently covers the core dependencies shipped
with Zope and is limited to the new WSGI based publisher.

Migrating an existing ZODB to Python 3 is not an automated process. You have
to update to Zope 4 first, see :ref:`zope4migration`.


WSGI as the new default server type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Zope 2.13 first gained support for running Zope as a WSGI application,
using any WSGI capable web server instead of the built-in ZServer.

Zope 4.0 takes this one step further and uses WSGI as the default
setup. Functional testing (testbrowser) support also uses the new
WSGI publisher.

The ZServer based publisher got moved into its own optional project.
So if you rely on ZServer features, like FTP, zdaemon or zopectl
support, please make sure to install ZServer and use its ``mkzopeinstance``
script to create a Zope instance.

The ZServer project also includes limited functional testing support
in the ``ZServer.Testing`` sub-package. testbrowser support is exclusively
available based on the WSGI publisher, as a result of a switch from
the unmaintained mechanize project to WebTest.

By default Zope only ships with a new ``mkwsgiinstance`` script which
creates a Zope instance configured to run as a WSGI application. The
example configuration uses the ``waitress`` web server, but Zope can
be run using any WSGI capable web server.

To make running Zope easier, a new ``runwsgi`` command line script got
added, which can read a PasteDeploy configuration and create and run
the WSGI pipeline specified in it. By default such a configuration is
created in the ``etc/zope.ini`` file. The ``runwsgi`` script supports
both ``-v`` / ``--verbose`` and ``-d`` / ``--debug`` arguments to print
out more information on the console. The debug argument enables Zope's
debug mode and disables the catch-all part of the httpexceptions
WSGI middleware. This means unexpected and uncaught exceptions show
their full traceback on the console and make it easier to debug them.
Without debug mode, these exceptions result in a 500 Internal Server
Error rendered as a normal HTML response.

.. note::

    In case you experience an ``HTTP 500: Internal Server Error``, where you
    would expect a ``Redirect``, the following might help you.

    Although the ``zope.ini`` created by ``mkwsgiinstance`` includes
    ``egg:Zope#httpexceptions`` as part of the pipeline, this might not be
    sufficient for existing projects. In case your project has configured a
    middleware handling and creating error views for HTTP exceptions, you need
    to make sure that ``egg:Zope#httpexceptions`` runs before that middleware.
    Otherwise a ``Redirect`` might not be handled as such. This can result in a
    non-functional ZMI.

The WSGI support has no built-in support for running as a daemon.
Your chosen WSGI server might support this or you can use external
projects like supervisord or systemd.

The WSGI support in Zope 4 has changed in a number of ways to make it
more similar to its ZServer equivalent. In Zope 2.13 the WSGI support
required using repoze WSGI middlewares to add transaction and retry
handling. The WSGI support in Zope 4 no longer supports those middlewares
but integrates transaction and retry handling back into the publisher
code. This allows it to also add back full support for publication events
and exception views. It does mean that the transaction is begun and
committed or aborted inside the publisher code and you can no longer
write WSGI middlewares that take part in the transaction cycle, but
instead have to use Zope specific hooks like you do in the ZServer
based publisher.


View component Acquisition changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In Zope 2.12 Zope Toolkit view components changed and stopped inheriting
from Acquisition base classes, as Acquisition got aware of `__parent__`
pointers, which meant that ``aq_parent(view)`` worked, without the view
having to mix-in an Acquisition base class. For backwards compatibility
a new `AcqusitionBBB` class was mixed in, to continue to support calling
``view.aq_parent``. This backwards compatibility class has been removed
in Zope 4, so ``view.aq_parent`` no longer works and you have to use
``aq_parent(view)``. The same applies for other view components like
view page template files or viewlets.


Page Templates now rendered by Chameleon
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Chameleon is an alternative implementation of the page template language
supporting additional features and impressive template rendering speed.

So far it was available via the `five.pt` project. In Zope 4 the code
from `five.pt` has been merged into Zope core and the Chameleon based
engine is now the default, removing the need to install `five.pt`
manually.

.. note::

   The page template language parser in Chameleon is extremely strict.
   For example, in Zope 2, the parser does not care about opening and closing
   tags that are not matched in terms of being uppercase/lowercase, or
   unmatched opening/closing tags in general. All this will now cause template
   compilation to fail. See :ref:`zope4pagetemplatemigration` for help.


Lower memory consumption at runtime
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Zope 4 depends on a new DateTime release. The new release has been optimized
for better memory use. Applications using a lot of DateTime values like the
Plone CMS have seen total memory usage to decrease by 10% to 20% for medium
to large deployments.


Simplified encoding configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
As it is reasonable to have one unified encoding in ZMI and frontend, support
for ``management_page_charset`` (as property of a folder) has been removed.
``default-zpublisher-encoding`` in `zope.conf` is the only place where to
define the site encoding that governs how the ZPublisher and Zope Page
Templates handle encoding and decoding of text.


Restyled Zope Management Interface (ZMI)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ZMI (Zope Management Interface) is now styled with Bootstrap.
See :ref:`ZMI-label` for details how to adapt Zope add-on packages to the new
styling.

.. figure:: /_static/folder_list.png
   :width: 1024
   :alt: The newly styled ZMI root

   The newly styled ZMI root

.. figure:: /_static/editor.png
   :width: 1024
   :alt: The `Ace` editor on a Page Template

   The `Ace` editor on a page template. The editor is also used for Python
   Scripts, DTML Methods/Documents and Z SQL Methods.

.. figure:: /_static/undo.png
   :width: 1024
   :alt: The central `Undo` view is reached from the new left-side menu

   The central `Undo` view is reached from the new left-side menu

.. figure:: /_static/properties.png
   :width: 1024
   :alt: The restyled `Properties` view

   The restyled `Properties` view
