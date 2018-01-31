Running Zope2 as a WSGI Application
===================================


This document assumes you have installed Zope into a ``virtualenv`` (see
:doc:`INSTALL-virtualenv`).

Install the Supporting Software
-------------------------------

To run as a WSGI application, you need to install some additional software.

.. code-block:: sh

   $ bin/pip install \
    --no-binary zc.recipe.egg \
    -r https://zopefoundation.github.io/Zope/releases/2.13.27/requirements.txt \
    repoze.who repoze.tm2 repoze.retry Paste PasteDeploy PasteScript
   Collecting repoze.who
   ...
   Successfully installed ...


Update the Zope Application Configuration
-----------------------------------------

The generated ``etc/zope.conf`` file assumes that Zope will be running
using the built-in ``ZServer``.

.. code-block:: sh

   $ vim etc/zope.conf

Update the contents as follows.

.. code-block:: apacheconf

   %define INSTANCE /path/to/virtualenv
   instancehome $INSTANCE

.. note::

   The ``%define instance /path/to/virtualenv`` element must
   point to the environment:  there is no "relative to this file" support
   built in.

Set up logging for the application.

.. code-block:: apacheconf

   <eventlog>
     level info
     <logfile>
       path $INSTANCE/log/event.log
       level info
     </logfile>
   </eventlog>

   <logger access>
     level WARN
     <logfile>
       path $INSTANCE/log/Z2.log
       format %(message)s
     </logfile>
   </logger>

Configure the database (note that you could use ``ZEO`` or ``Relstorage``
rather than a bare ``FileStorage``):

.. code-block:: apacheconf

   <zodb_db main>
       # Main FileStorage database
       <filestorage>
         # See .../ZODB/component.xml for directives (sectiontype
         # "filestorage").
         path $INSTANCE/var/Data.fs
       </filestorage>
       mount-point /
   </zodb_db>

   <zodb_db temporary>
       # Temporary storage database (for sessions)
       <temporarystorage>
         name temporary storage for sessioning
       </temporarystorage>
       mount-point /temp_folder
       container-class Products.TemporaryFolder.TemporaryContainer
   </zodb_db>

Because we will be running a separately-configured WSGI server, remove any
``<http-server>`` configuration from the file.

Create the WSGI Server Configuration
------------------------------------

.. code-block:: sh

   $ vim etc/zope.wsgi


First, configure the "application" endpoint for Zope:

.. code-block:: ini

   [app:zope]
   use = egg:Zope2#main
   zope_conf = %(here)s/zope.conf


Next, set up the WSGI middleware pipeline:

.. code-block:: ini

   [pipeline:main]
   pipeline =
       egg:paste#evalerror
       egg:repoze.retry#retry
       egg:repoze.tm2#tm
       zope

The middleware layers are "wrapped" around the application endpoint as follows:

- ``paste#evalerror`` is debugging middleware, which shows tracebacks for
  errors raised from the application.  It should **not** be configured for
  production use.

- ``repoze.retry#retry`` is middleware which retries requests when retriable
  exceptions are raised.  By default, it retries 3 times, and only for
  requests which raise ``ZODB.ConflictError``.  See
  http://repozeretry.rtfd.org/ for details on configuring it otherwise.

- ``repoze.tm2#tm`` is middleware which begins a new transaction for each
  request, and then either aborts the transaction (if the request raises an
  exception) or commits it (if not).  See
  http://repozetm2.rtfd.org/ for details on configuring it.

Finally, configure the WSGI server:

.. code-block:: ini

   [server:main]
   use = egg:paste#http
   host = localhost
   port = 8080

.. note::

   Any server conforming to PEP 333/3333 should work, although the parameters
   could change.


Set up the Admin User
---------------------

Before starting the WSGI server, run the ``addzope2user`` script to configure
the administrative user.

.. code-block:: sh

   $ bin/addzope2user admin <yourpasswordhere>
   No handlers could be found for logger "ZODB.FileStorage"
   User admin created.


Start the WSGI Server
---------------------

.. code-block:: sh

   $ bin/paster serve etc/zope.wsgi
   Starting server in PID 24934.
   serving on http://127.0.0.1:8080

Running Other Applications in the same WSGI Server Process
----------------------------------------------------------

You can use any of the normal ``Paste`` WSGI features to combine Zope and
other WSGI applications inside the same server process.  E.g., the following
configuration uses the
`composite application <http://pythonpaste.org/deploy/#composite-applications>`_
support offered by ``PasteDeploy`` to host Zope at the ``/`` prefix,
with static files served from disk at ``/static``:

.. code-block:: ini

   [app:zope-app]
   use = egg:Zope2#main
   zope_conf = %(here)s/zope.conf

   [pipeline:zope-pipeline]
   pipeline =
       egg:paste#evalerror
       egg:repoze.retry#retry
       egg:repoze.tm2#tm
       zope-app

   [app:static]
   use = egg:Paste#static
   document_root = %(here)s/static

   [composite:main]
   use = egg:Paste#urlmap
   / = zope-pipeline
   /static = static
