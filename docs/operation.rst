Configuring and Running Zope
============================
Whichever method you used to install Zope and create a server instance (see
:doc:`INSTALL`), the end result is configured and operated the same way.

.. note::

   If you have installed Zope using ``zc.buildout`` in conjunction with
   ``plone.recipe.zope2instance`` as outlined in :doc:`INSTALL`, many of
   the following tasks are already done for you and some others differ
   slightly. You can immediately skip down to `Running Zope
   (plone.recipe.zope2instance install)`.


Creating a Zope instance
------------------------

Once you've installed Zope, you will need to create an "instance
home". This is a directory that contains configuration and data for a
Zope server process.  The instance home is created using the
``mkwsgiinstance`` script:

.. code-block:: console

  $ bin/mkwsgiinstance -d .

The `-d` argument specifies the directory to create the instance
home in, where the dot (``.``) means the current folder.

You will be asked to provide a user name and password for an
administrator's account during ``mkwsgiinstance``.  To see all available
command-line options, run the script with the ``--help`` option:

.. code-block:: console

  $ bin/mkwsgiinstance --help

If you followed the example and chose the current directory, you'll
find the instances files in the subdirectories of the ``virtualenv``:

- ``etc/`` will hold the configuration files.
- ``var/`` will hold the database files.
- ``var/log`` will hold log files.


Filesystem Permissions
----------------------
You need to set permissions on the directory Zope uses to store its
data. This will normally be the `var` directory in the instance home.
Zope needs to read and write data to this directory. Before
running Zope you should ensure that you give adequate permissions
to this directory for the user id Zope will run under.

Do not run Zope as root. Either create a user specifically for Zope or use
an existing account with non-admin privileges.


Configuring Zope
----------------

Your instance's configuration is defined in its ``etc/zope.conf``
and ``etc/zope.ini`` configuration files.

.. note::

    Any changes in these configuration files require you to restart your Zope
    instance before they become active.

``zope.ini``: WSGI configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The file ``etc/zope.ini`` contains all settings related to the `WSGI` pipeline,
the `WSGI` server and logging.

When starting Zope, if you see errors indicating that an address is in
use, then you may have to change the ports Zope uses for HTTP.
The default HTTP port used by Zope is 8080. You can change the port
used by editing the ``[server]`` configuration section, which defines settings
for the `WSGI` server itself:

.. code-block:: ini

  [server:main]
  use = egg:waitress#main
  host = 127.0.0.1
  port = 8080

See the section `Using alternative WSGI server software`_ to learn how to
integrate `WSGI` servers other than the default ``waitress``.

Zope is configured in the ``[app]`` section. It defines the so-called "entry
point" called by the `WSGI` server and where the Zope configuration file
``zope.conf`` is located:

.. code-block:: ini

   [app:zope]
   use = egg:Zope#main
   zope_conf = /path/to/zope.conf

The logging configurations are part of the ``etc/zope.ini`` file as well.
The default configurations created by ``mkwsgiinstance`` and
``plone.recipe.zope2instance`` are suitable for most applications.
The `Python Logging Cookbook
<https://docs.python.org/3/howto/logging-cookbook.html>`_ has a great
selection of topics for advanced configurations.

Keep in mind that different WSGI servers have different logging behaviors.
Some have their own access and event logging, some don't log anything at all.
For good control over your application's logging needs, the default
configurations use the ``translogger`` WSGI middleware from the ``Paste``
package. It can capture and log all errors propagating from your application.

.. note ::

   If your application is created using a custom ``zc.buildout`` configuration
   and you want to use ``translogger`` for logging, make sure to specify
   the ``wsgi`` extra for Zope in your buildout's ``eggs`` specification,
   like ``Zope[wsgi]``.

``zope.conf``: Zope settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You configure Zope itself in ``etc/zope.conf``.

For a full description of the supported sections and directives for
``zope.conf``, refer to the :ref:`configuration reference section
<configuration_reference>`.


Running Zope
------------

Running Zope in the foreground
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To run Zope without detaching from the console, use:

.. code-block:: console

   $ bin/runwsgi -v etc/zope.ini
   Starting server in PID 24934.
   serving on http://127.0.0.1:8080

In this mode, Zope emits its log messages to the console, and does not
detach from the terminal.

By default this command does not enable Zope's debug mode, so it can
be used for production.

In order to enable debug mode, you can add the additional ``-d`` or
``--debug`` argument to the command:

.. code-block:: console

   $ bin/runwsgi -dv etc/zope.ini
   Starting server in PID 55111.
   serving on http://127.0.0.1:8080

The runwsgi commands takes a PasteDeploy configuration file as its
argument. You can configure different WSGI capable servers,
the WSGI pipeline or logging configuration in this file.

Now you are able to log in using a browser, as described in
`Logging In To Zope`_.


Running Zope as a Daemon
~~~~~~~~~~~~~~~~~~~~~~~~
Zope itself has no built-in support for running as a daemon anymore.

If you create your Zope instance using ``plone.recipe.zope2instance`` you can
use its start/stop script to daemonize Zope. See the next section for how to do
that.

Alternatively, you can use projects like supervisord to achieve this or use
your operating system's built-in process manager, like ``systemd`` on most
Linux versions. As an example, the following ``systemd`` service configuration
works with the ``runwsgi`` script. It assumes your buildout is located at
``/opt/zopeinstance`` and the user account your Zope instance runs under is
``zope``:

.. code-block:: cfg

   [Unit]
   Description=Zope client zopeinstance
   After=network.target

   [Service]
   Type=simple
   User=zope
   ExecStart=/opt/zopeinstance/bin/runwsgi /opt/zopeinstance/etc/zope.ini
   KillMode=control-group
   TimeoutStartSec=10
   TimeoutStopSec=10

   [Install]
   WantedBy=multi-user.target

Save this configuration under ``/etc/systemd/system/zopeinstance.service`` and
execute ``systemctl daemon-reload`` for ``systemd`` to read it. After that you
can use standard ``systemctl`` commands to start, restart or stop the Zope
instance:

.. code-block:: console

   [root@server]# systemctl start zopeinstance
   [root@server]# systemctl restart zopeinstance
   [root@server]# systemctl status zopeinstance
   [root@server]# systemctl stop zopeinstance
   ...


Debugging Zope
~~~~~~~~~~~~~~
In order to debug the Zope application, it can be helpful to connect
to its database and inspect or change it on the command line. This
feature was previously available via the dedicated `zopectl debug`
command - in the new WSGI setup this is available via the `zconsole`
module and console script:

.. code-block:: console

  $ bin/zconsole debug etc/zope.conf
  >>> app
  <Application at >

  >>> app.acl_users
  <UserFolder at /acl_users>

  >>> import transaction
  >>> transaction.begin()
  >>> app.acl_users._doAddUser('foo', 'bar', ['Manager'], [])
  <User 'foo'>
  >>> transaction.commit()

Running scripts
~~~~~~~~~~~~~~~
This was previously availabe using `zopectl run <path_to_script> <scriparg1> ...`.
Again in the WSGI setup the `zconsole` module and console script can be used:

.. code-block:: console

  $ bin/zconsole run etc/zope.conf <path_to_script> <scriptarg1> ...


Adding users
~~~~~~~~~~~~
If you need to add a Manager to an existing Zope instance, you can do
this using ``addzopeuser`` as follows:

.. code-block:: console

  $ bin/addzopeuser user password

The script expects to find the configuration file at ``etc/zope.conf`` by default.
If it is located in a different location you can specify it with the `--configuration` option:

.. code-block:: console

  $ bin/addzopeuser --configuration /path/to/etc/zope.conf user password


Running Zope (plone.recipe.zope2instance install)
-------------------------------------------------
Scipt names and invocations vary slightly in installations that use
``plone.recipe.zope2instance``, but the outcome is the same as described above.
The following examples assume that the name of the buildout section was
``zopeinstance``.

Running Zope in the foreground
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To run Zope without detaching from the console, use:

.. code-block:: console

   $ bin/zopeinstance fg
   ...
   Serving on http://127.0.0.1:8080


Running Zope as a Daemon
~~~~~~~~~~~~~~~~~~~~~~~~
The ``zopeinstance`` runner script can daemonize the Zope process:

.. code-block:: console

   $ bin/zopeinstance start
   ...
   daemon process started, pid=60116

Here's how to get status information and how to stop the Zope instance:

.. code-block:: console

   $ bin/zopeinstance status
   program running; pid=60116
   $ bin/zopeinstance stop
   ...
   daemon process stopped


To have your instance start automatically upon reboot, you will need to
integrate with your operating system's service startup facility. As an example,
the following ``systemd`` service configuration works with the start/stop
script generated by ``plone.recipe.zope2instance``. It assumes the script name
is ``zopeinstance``, your buildout is located at ``/opt/zopeinstance`` and the
user account your Zope instance runs under is ``zope``:

.. code-block:: cfg

   [Unit]
   Description=Zope client zopeinstance
   After=network.target

   [Service]
   Type=forking
   User=zope
   ExecStart=/opt/zopeinstance/bin/zopeinstance start
   PIDFile=/opt/zopeinstance/var/zopeinstance/Z4.pid
   ExecStop=/opt/zopeinstance/bin/zopeinstance stop
   ExecReload=/opt/zopeinstance/bin/zopeinstance stop && /opt/zopeinstance/bin/zopeinstance start
   KillMode=control-group
   TimeoutStartSec=10
   TimeoutStopSec=10

   [Install]
   WantedBy=multi-user.target

Save this configuration under ``/etc/systemd/system/zopeinstance.service`` and
execute ``systemctl daemon-reload`` for ``systemd`` to read it. After that you
can use standard ``systemctl`` commands to start, restart or stop the Zope
instance:

.. code-block:: console

   [root@server]# systemctl start zopeinstance
   [root@server]# systemctl restart zopeinstance
   [root@server]# systemctl status zopeinstance
   [root@server]# systemctl stop zopeinstance
   ...


Debugging Zope
~~~~~~~~~~~~~~
Debugging can be done at the command line:

.. code-block:: console

  $ bin/zopeinstance debug
  Starting debugger (the name "app" is bound to the top-level Zope object)
  >>> app
  <Application at >

  >>> app.acl_users
  <OFS.userfolder.UserFolder object at ...>

  >>> import transaction
  >>> transaction.begin()
  >>> app.acl_users._doAddUser('foo', 'bar', ['Manager'], [])
  <User 'foo'>
  >>> transaction.commit()


Running scripts
~~~~~~~~~~~~~~~
You can run Python scripts from the command line. The name ``app`` is injected
into the top level namespace, it represents the root application object for
your site.

.. code-block:: console

  $ bin/zopeinstance run <path_to_script> <scriptarg1> ...


Adding users
~~~~~~~~~~~~
If you need to add a Manager to an existing Zope instance:

.. code-block:: console

  $ bin/zopeinstance adduser user password
  Created user: user


Logging In To Zope
------------------

Once you've started Zope, you can then connect to the Zope webserver
by directing your browser to::

  http://yourhost:8080/manage

where 'yourhost' is the DNS name or IP address of the machine
running Zope.  If you changed the HTTP port as described, use the port
you configured.

You will be prompted for a user name and password. Use the user name
and password you provided in response to the prompts issued during
the Zope instance creation, or configured into your buildout configuration
for installs based on ``plone.recipe.zope2instance``.

Now you're off and running! You should be looking at the Zope
management screen which is divided into two frames. On the left you
can navigate between Zope objects and on the right you can edit them
by selecting different management functions with the tabs at the top
of the frame.

To create content to be rendered at http://yourhost:8080/ create a `Page
Template` or `DTML Document` named ``index_html``.


Special access user accounts
----------------------------

The Initial User
~~~~~~~~~~~~~~~~
An initial username and password is needed to "bootstrap" the creation of
normal managers of your Zope site. This is accomplished through the
use of the 'inituser' file in the directory specified as the instance
home.

The first time Zope starts, it will detect that no users have been
defined in the root user folder.  It will search for the 'inituser'
file and, if it exists, will add the user defined in the file to the
root user folder.

Normally, 'inituser' is created by the ``makewsgiinstance`` install
script.


The super user ("break glass in emergency" user)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you find yourself locked out of your Zope instance you can create a user
by placing a file named ``access`` in the directory specified as the instance
home. The file has one line with a colon-separated login and password, like:

.. code-block:: console

  superuser:mysecretpassword

Now restart Zope and use these credentials to log in. This type of user account
cannot create any content, but it can add new users to the user folder or edit
existing users to get you out of a bind.

Do not forget to delete the ``access`` file and restart Zope when you are
done.


Troubleshooting
---------------

- This version of Zope requires Python 3.9 and later.
  It will *not* run with any version of PyPy.

- To build Python extensions you need to have Python configuration
  information available. If your Python comes from an RPM you may
  need the python-devel (or python-dev) package installed too. If
  you built Python from source all the configuration information
  should already be available.

- See the :doc:`changes` for important notes on this version of Zope.


.. _configuration_reference:


Using alternative WSGI server software
--------------------------------------
The WSGI integration gives you a choice of WSGI server software to run your
Zope application. This section lists several options that were selected
because they either have a `PasteDeploy` entry point or have one provided by
shim software, which means they work with the default Zope scripts for
starting/stopping the service.


Things to watch out for
~~~~~~~~~~~~~~~~~~~~~~~
The ZODB uses connection pooling where a working thread grabs a connection
from the pool to serve content and then releases it when the work is done.
The default size of this connection pool is 7. You should choose a number of
application threads that stays safely below that number of ZODB connections.
If the WSGI server lets you configure the number of threads, 4 is a safe
choice.

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
- standard Zope 5.9 instances, one with ZEO and one without
- Python 3.11.7 on macOS Sonoma/14.2.1
- standard WSGI server configurations, the only changes are to number of
  threads and/or number of workers where available.

This load test uncovered several issues:

- ``cheroot`` (tested version: 10.0.0) seemed overwhelmed by the load. It kept
  resetting connections to the test client with an error rate of about 1.5%.
- ``gunicorn`` (tested version: 19.9.0) does not work at all with ZEO. Without
  ZEO it only works if a single worker is configured. Even with a single thread
  client connections timed out, the failure rate was about 0.25%.
- ``bjoern`` (tested version: 3.2.2) is the clear speed winner with 3,870
  requests/second against both the ZEO and non-ZEO Zope instance.
- ``waitress`` (tested version: 2.1.12) is the all-around best choice. It's
  just about 15% slower than ``bjoern``, but both the built-in WSGI tools as
  well as ``plone.recipe.zope2instance`` use it as the default and make it very
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


Debugging Zope applications under WSGI
--------------------------------------
You can debug a WSGI-based Zope application by adding a statement to activate
the debugger. In addition, you can take
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


Zope configuration reference
----------------------------

.. zconfig:: Zope2.Startup
    :file: wsgischema.xml


