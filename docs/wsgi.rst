Zope and WSGI
=============
Starting with Zope 4, a WSGI-compatible application entry point is the default
option for serving your site. Zope comes with a set of scripts to set up a
default WSGI stack with ``waitress`` as WSGI server, but any other WSGI server
can be used.

.. contents::
   :local:


WSGI application entry points
-----------------------------
To use Zope as an application in a PasteDeploy-style ``.ini`` configuration
file, use the ``Zope#main`` entry point and specify a path to a Zope
configuration file:

.. code-block:: ini

   [app:zope]
   use = egg:Zope#main
   zope_conf = /path/to/zope.conf

To compose your pipeline in Python code:

.. code-block:: python

   from Zope2.startup.run import make_wsgi_app

   app = make_wsgi_app({}, '/path/to/zope.conf')


Building a Zope instance with WSGI support
------------------------------------------
Zope ships with several helper scripts to set up a default WSGI-enabled
environment. The document :doc:`operation` walks you through using
``mkwsgiinstance`` for a default configuration that you can use in conjunction
with the ``runwsgi`` script to start a Zope instance. 

The buildout extension ``plone.recipe.zope2instance`` expands on that and
adds a script wrapper for convenient starting and stopping as well as a host
of other functions. Take a look at `their PyPI page listing all options
<https://pypi.org/project/plone.recipe.zope2instance/>`_.


Logging configuration
---------------------
When running Zope under the old ZServer, logging configurations were built in.
Now they are explicit and part of the WSGI configuration ``.ini`` file. The
default configurations created by ``mkwsgiinstance`` and
``plone.recipe.zope2instance`` are suitable for most applications.

Keep in mind that different WSGI servers have different logging behaviors. Some
have their own access and event logging, some don't log anything at all. For
good control over your application's logging needs, the default configurations
use the ``translogger`` WSGI middleware from the ``Paste`` package. It can
capture and log all errors propagating from your application.

.. note ::

   If your application is created using a custom ``zc.buildout`` configuration
   and you want to use ``translogger`` for logging, make sure to include the
   ``Paste`` egg in your buildout's ``eggs`` specification.

You can use the generated default WSGI configuration's logging sections as a
starting point for changes. The `Python Logging Cookbook 
<https://docs.python.org/3/howto/logging-cookbook.html>`_ has a great selection
of topics for advanced configurations.


Choosing WSGI server software
-----------------------------
The WSGI integration gives you a choice of WSGI server software to run your
Zope application. This section lists several options that were selected
because they either have a `PasteDeploy` entry point or have one provided by
shim software, which means they work with the default Zope scripts for
starting/stopping the service.


Things to watch out for
~~~~~~~~~~~~~~~~~~~~~~~
The ZODB uses connection pooling where a working thread grabs a connection
from the pool to serve content and then releases it when the work is done.
The default size of this connection pool is 7. The advice from ``ZServer``
days to choose a number of application threads that stays safely below that
number of ZODB connections is still valid. ``ZServer`` used 4 threads by
default, so if the WSGI server lets you configure the number of threads 4 is
still a safe choice.

Another recommendation from Zope 2 is still valid as well: If you have a choice
between less Zope instances with a higher number of threads each, or more
instances with less threads each, choose the latter. Create more separate Zope
instances and set the WSGI server threads value to e.g. 2.

.. warning::

   If the WSGI server software lets you configure a number of worker processes,
   like ``gunicorn`` does, do not configure more than a single worker.
   Otherwise you will see issues due to concurrent ZODB access by more than
   one process, which may corrupt your ZODB.


Test criteria for recommendations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A simple contrived load test was done with the following parameters:

- 100 concurrent clients accessing Zope
- 100 seconds run time
- the clients just fetch "/"
- standard Zope 4 instances, one with ZEO and one without
- Python 2.7.16 on macOS Mojave/10.14.4
- standard WSGI server configurations, the only changes are to number of
  threads and/or number of workers where available.

This load test uncovered several issues:

- ``cheroot`` (tested version: 6.5.5) was magnitudes slower than all others.
  Unlike the others, it did not max out CPU. It is unclear where the slowdown
  originates. Others reached 500-750 requests/second. ``cheroot`` only served
  12 requests/second per configured thread.
- ``gunicorn`` (tested version: 19.9.0) showed very strange behavior against
  the non-ZEO Zope instance. It serves around 500 requests/second, but then
  hangs and serves no requests for several seconds, before picking up again.
- ``gunicorn`` (tested version: 19.9.0) does not like the ZEO instance at all.
  No matter what configuration in terms of threads or workers was chosen
  ``gunicorn`` just hung so badly that even CTRL-C would not kill it.
  Switching to an asynchronous type of worker (tested with ``gevent``)
  did not make a difference.
- ``werkzeug`` (tested version: 0.15.2) does not let you specify the number
  of threads, you only tell it to use threads or not. In threaded mode it
  spawns too many threads and immedialy runs up agains the ZODB connection
  pool limits, so with Zope only the unthreaded mode is suitable. Even in
  unthreaded mode, the service speed was inconsistent. Just like ``gunicorn``
  it had intermittent hangs before recovering.
- ``bjoern`` (tested version: 3.0.0) is the clear speed winner with 740
  requests/second against both the ZEO and non-ZEO Zope instance, even though
  it is single-threaded.
- ``waitress`` (tested version: 1.3.0) is the all-around best choice. It's
  just 10-15% slower than ``bjoern``, but both the built-in WSGI tools as well
  as ``plone.recipe.zope2instance`` use it as the default and make it very
  convenient to use.


Recommended WSGI servers
~~~~~~~~~~~~~~~~~~~~~~~~

waitress (the default and recommended choice)
+++++++++++++++++++++++++++++++++++++++++++++
If you create a Zope instance using the ``mkwsgiinstance`` script described
above or the ``plone.recipe.zope2instance`` buildout recipe, you will
automatically get a ``waitress``-based server. The default configurations set
up for you will be sufficient for most applications. See the `waitress
documentation <https://docs.pylonsproject.org/projects/waitress/>`_ for
additional information.

.. warning::

   The WSGI server Zope uses by default, waitress, was
   affected by `an important security issue
   <https://github.com/Pylons/waitress/security/advisories/GHSA-4f7p-27jc-3c36>`_.
   The fixed version 2.1.1 is only compatible with Python 3.7 and higher. We
   strongly advise you to either upgrade your Zope 4 installation to at least
   Python 3.7, move to Zope 5 on Python 3.7 or higher, or `switch to a
   different WSGI server
   <https://zope.readthedocs.io/en/latest/operation.html#recommended-wsgi-servers>`_.

Here's a very simple configuration using ``plone.recipe.zope2instance``:

.. code-block:: ini

   [zopeinstance]
   recipe = plone.recipe.zope2instance
   eggs =
   zodb-temporary-storage = off
   user = admin:password
   http-address = 8080

Note the empty ``eggs`` section, you cannot leave it out.

``waitress`` has many options that you can add to the buildout section. A full
list is `part of the waitress documentation
<https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html>`_.


bjoern (the fastest)
++++++++++++++++++++
The `bjoern WSGI server <https://github.com/jonashaag/bjoern>`_ can be
integrated using a shim package called `dataflake.wsgi.bjoern
<https://dataflakewsgibjoern.readthedocs.io/>`_. See the `Using this package`
section for details on how to integrate `bjoern` using Zope's own
``runwsgi`` script and how to create a suitable WSGI configuration.

If you use ``plone.recipe.zope2instance``, the following
section will pull in the correct dependencies:

.. code-block:: ini

   [zopeinstance]
   recipe = plone.recipe.zope2instance
   eggs =
       dataflake.wsgi.bjoern
   zodb-temporary-storage = off
   user = admin:password
   http-address = 8080
   wsgi = ${buildout:directory}/etc/bjoern.ini


Problematic WSGI servers
~~~~~~~~~~~~~~~~~~~~~~~~

werkzeug
++++++++
`werkzeug <https://palletsprojects.com/p/werkzeug/>`_ is a WSGI library that
contains not just a WSGI server, but also a powerful debugger. It can
easily integrate with Zope using a shim package called `dataflake.wsgi.werkzeug 
<https://dataflakewsgiwerkzeug.readthedocs.io/>`_. See the `Using this package`
section for how to integrate `werkzeug` using Zope's own ``runwsgi`` script and
how to create a suitable WSGI configuration.

If you use ``plone.recipe.zope2instance``, the following section will pull in
the correct dependencies, after you have created a WSGI configuration file:

.. code-block:: ini

   [zopeinstance]
   recipe = plone.recipe.zope2instance
   eggs =
       dataflake.wsgi.werkzeug
   zodb-temporary-storage = off
   user = admin:password
   http-address = 8080
   wsgi = ${buildout:directory}/etc/werkzeug.ini


gunicorn
++++++++
The `gunicorn WSGI server <https://gunicorn.org/>`_ has a built-in
`PasteDeploy` entry point and integrates easily. The following example buildout
configuration section will create a ``bin/runwsgi`` script that uses
`gunicorn`.

.. code-block:: ini

   [gunicorn]
   recipe = zc.recipe.egg
   eggs =
       Zope
       gunicorn
   scripts =
       runwsgi

You can use this script with a WSGI configuration file that you have to create
yourself. Please see the `gunicorn documentation
<https://docs.gunicorn.org/>`_, especially the `Configuration File` section on
`Configuration Overview`, for Paster Application configuration information. A
very simple server configuration looks like this:

.. code-block:: ini

   [server:main]
   use = egg:gunicorn#main
   host = 192.168.0.1
   port = 8080
   proc_name = zope

You can then run the server using ``runwsgi``:

.. code-block:: console

   $ bin/runwsgi etc/gunicorn.ini
   2019-04-22 11:45:39 INFO [Zope:45][MainThread] Ready to handle requests
   Starting server in PID 84983.

.. note::
   gunicorn version 19.9.0 or less will print an ominous warning message on the
   console upon startup that seems to suggest their WSGI entry point is
   deprecated in favor of using their own built-in scripts. This is misleading.
   Future versions will not show this message.

If you use ``plone.recipe.zope2instance``, you can make it use `gunicorn` by
adding its egg to the buildout section and setting the WSGI configuration file
path to the path of the configuration file you created yourself:

.. code-block:: ini

   [zopeinstance]
   recipe = plone.recipe.zope2instance
   eggs =
       gunicorn
   zodb-temporary-storage = off
   user = admin:password
   http-address = 8080
   wsgi = ${buildout:directory}/etc/gunicorn.ini


cheroot
+++++++
The `cheroot WSGI server <https://cheroot.cherrypy.org>`_ can be integrated
using a shim package called `dataflake.wsgi.cheroot
<https://dataflakewsgicheroot.readthedocs.io/>`_. See the `Using this package`
section for details on how to integrate `cheroot` using Zope's own
``runwsgi`` script and how to create a suitable WSGI configuration.

If you use ``plone.recipe.zope2instance``, the following
section will pull in the correct dependencies:

.. code-block:: ini

   [zopeinstance]
   recipe = plone.recipe.zope2instance
   eggs =
       dataflake.wsgi.cheroot
   zodb-temporary-storage = off
   user = admin:password
   http-address = 8080
   wsgi = ${buildout:directory}/etc/cheroot.ini


Debugging Zope applications under WSGI
--------------------------------------
You can debug a WSGI-based Zope application the same way you have debugged
ZServer-based installations in the past. In addition, you can now take
advantage of WSGI middleware or debugging facilities built into the chosen
WSGI server.

When developing your application or debugging, which is the moment you want to
use debugging tools, you can start your Zope instance in `exceptions debug
mode`. This will disable all registered exception views including
``standard_error_message`` so that exceptions are not masked or hidden.

This is how you run Zope in exceptions debug mode using the built-in
``runwsgi`` script:

.. code-block:: console

   $ bin/runwsgi -e etc/zope.ini

If you built your environment using ``plone.recipe.zope2instance`` you will
need to do a manual change to your Zope configuration file. Enable exceptions
debug mode by adding the ``debug-exceptions on`` setting before starting your
application. The example presumes the Zope instance was named ``zopeinstance``,
your Zope configuration file will be at `parts/zopeinstance/etc/zope.conf`.

.. code-block:: console

   bin/zopeinstance fg

With Zope set up to let WSGI handle exceptions, these are a few options for the
WSGI pipeline:

If you use ``waitress``, you can make it output exception tracebacks in the
browser by configuring ``expose_tracebacks``. The keyword works in both
standard and ``plone.recipe.zope2instance`` configurations:

.. code-block:: ini

   [server:main]
   use = egg:waitress#main
   host = 127.0.0.1
   port = 8080
   expose_tracebacks = True

   ... or ...

   [server:main]
   paste.server_factory = plone.recipe.zope2instance:main
   use = egg:plone.recipe.zope2instance#main
   listen = 0.0.0.0:8080
   threads = 2
   expose_tracebacks = True

``werkzeug`` includes a full-featured debugging tool. See the
`dataflake.wsgi.werkzeug documentation
<https://dataflakewsgiwerkzeug.readthedocs.io/en/latest/usage.html#using-the-werkzeug-debugger>`_
for how to enable the debugger. Once you're up and running, the `werkzeug
debugger documentation
<https://werkzeug.palletsprojects.com/en/0.15.x/debug/#using-the-debugger>`_
will show you how to use it.


WSGI documentation links
------------------------
- the WSGI standard is described in `PEP-3333
  <https://www.python.org/dev/peps/pep-3333/>`_.
- The WSGI website at https://wsgi.readthedocs.io/ is comprehensive but also
  rather outdated.
- AppDynamics did an interesting `WSGI server performance analysis
  <https://blog.appdynamics.com/engineering/a-performance-analysis-of-python-wsgi-servers-part-2/>`_.
