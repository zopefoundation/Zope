Configuring and Running Zope
============================

.. note::

    New installations should use Zope 5 instead of Zope 4. Users migrating
    applications from Zope 2 should upgrade to Zope 5 once their application
    supports Zope 4 on Python 3. The Zope developer community strives to make
    sure the next upgrade step to Zope 5 is and remains a quick and painless
    exercise.


Whichever method you used to install Zope and create a server instance (see
:doc:`INSTALL`), the end result is configured and operated the same way.

.. note::

   If you have installed Zope using ``zc.buildout`` in conjunction with
   ``plone.recipe.zope2instance`` as outlined in :doc:`INSTALL`, many of
   the following tasks are already done for you and some others differ
   slightly. You can immediately skip down to `Running Zope`.

.. contents::
   :local:


Creating a Zope instance
------------------------

.. attention::

  The following steps describe how to install a WSGI based Zope instance.
  If you want/have to use ZServer instead of WSGI (Python 2 only!) follow
  the documentation `Creating a Zope instance for Zope 2.13`_, as it has not
  changed since that version.

Once you've installed Zope, you will need to create an "instance
home". This is a directory that contains configuration and data for a
Zope server process.  The instance home is created using the
``mkwsgiinstance`` script:

.. code-block:: console

  $ bin/mkwsgiinstance -d .

The `-d .` argument specifies the directory to create the instance
home in.

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

When starting Zope, if you see errors indicating that an address is in
use, then you may have to change the ports Zope uses for HTTP.
The default HTTP port used by Zope is 8080. You can change the port
used by editing ./etc/zope.ini appropriately.

The section in the configuration file looks like this:

.. code-block:: ini

  [server:main]
  use = egg:waitress#main
  host = 127.0.0.1
  port = 8080

After making any changes to the configuration file, you need to restart any
running Zope server for the affected instance before changes are in effect.

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
Zope itself has no built-in support for running as a daemon any more.

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
this using `addzope2user` as follows:

.. code-block:: console

  $ bin/addzope2user user password

The script expects to find the configuration file at ``etc/zope.conf``.


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

- This version of Zope requires Python 2.7 or Python 3.5 and later.
  It will *not* run with any version of PyPy.

- To build Python extensions you need to have Python configuration
  information available. If your Python comes from an RPM you may
  need the python-devel (or python-dev) package installed too. If
  you built Python from source all the configuration information
  should already be available.

- See the :doc:`changes` for important notes on this version of Zope.


.. _configuration_reference:

Zope configuration reference
----------------------------

.. zconfig:: Zope2.Startup
    :file: wsgischema.xml


.. _`Creating a Zope instance for Zope 2.13` : http://zope.readthedocs.io/en/2.13/INSTALL-buildout.html#creating-a-zope-instance
