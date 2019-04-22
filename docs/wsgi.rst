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


WSGI tools and helpers for Zope
-------------------------------
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


WSGI server integrations
------------------------
This section describes how to integrate specific WSGI servers into your Zope
instance. These servers were chosen because they either have a `PasteDeploy`
entry point or have one provided by shim software, which means they work with
the default Zope scripts for starting/stopping the service.


waitress (the default)
~~~~~~~~~~~~~~~~~~~~~~
If you create a Zope instance using the ``mkwsgiinstance`` script described
above or the ``plone.recipe.zope2instance`` buildout recipe, you will
automatically get a ``waitress``-based server. The default configurations set
up for you will be sufficient for most applications. See the `waitress
documentation <https://docs.pylonsproject.org/projects/waitress/>`_ for
additional information.

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


gunicorn
~~~~~~~~
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
~~~~~~~
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


bjoern
~~~~~~
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


WSGI documentation links
------------------------
- the WSGI standard is described in `PEP-3333
  <https://www.python.org/dev/peps/pep-3333/>`_.
- The WSGI website at https://wsgi.readthedocs.io/ is comprehensive but also
  rather outdated.
- AppDynamics did an interesting `WSGI server performance analysis
  <https://blog.appdynamics.com/engineering/a-performance-analysis-of-python-wsgi-servers-part-2/>`_.
