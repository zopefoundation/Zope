Zope and WSGI
=============
Starting with Zope 4, a WSGI-compatible application entry point is the default
option for serving your site. Zope comes with a set of scripts to set up a
default WSGI stack with ``waitress`` as WSGI server, but any other WSGI server
can be used.


The WSGI application entry points
---------------------------------
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


Zope helpers to set up a default WSGI configuration
---------------------------------------------------
The Zope egg contains several helper scripts to set up a default WSGI-enabled
environment. The document :doc:`operation` walks you through using
``mkwsgiinstance`` for a default configuration that you can use in conjunction
with the ``runwsgi`` script to start a Zope instance. The buildout extension
``plone.recipe.zope2instance`` expands on that and adds a script wrapper for
convenient starting and stopping as well as a host of other functions.


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
