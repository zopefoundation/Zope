Configuring and Running Zope
============================

.. highlight:: bash

.. contents::


Whichever method you used to install Zope and create a server instance (see
:doc:`INSTALL-buildout` and :doc:`INSTALL-virtualenv`), the end result is
configured and operated the same way.


Configuring Zope
----------------

Your instance's configuration is defined in its ``etc/wsgi.conf``
and ``etc/zope.ini`` configuration files.

When starting Zope, if you see errors indicating that an address is in
use, then you may have to change the ports Zope uses for HTTP.
The default HTTP port used by Zope is 8080. You can change the port
used by editing ./etc/zope.ini appropriately.

The section in the configuration file looks like this::

  [server:main]
  use = egg:waitress#main
  host = 127.0.0.1
  port = 8080

After making any changes to the configuration file, you need to restart any
running Zope server for the affected instance before changes are in effect.

For a full description of the supported sections and directives for
``wsgi.conf``, refer to the machine readable schema description file
``https://rawgit.com/zopefoundation/Zope/master/src/Zope2/Startup/wsgischema.xml``.


Running Zope
------------

To run Zope without detaching from the console, use:

.. code-block:: sh

   $ bin/runwsgi -v etc/zope.ini
   Starting server in PID 24934.
   serving on http://127.0.0.1:8080

In this mode, Zope emits its log messages to the console, and does not
detach from the terminal.

By default this command does not enable Zope's debug mode, so it can
be used for production.

In order to enable debug mode, you can add the additional ``-d`` or
``--debug`` argument to the command:

.. code-block:: sh

   $ bin/runwsgi -v etc/zope.ini -d
   Starting server in PID 55111.
   serving on http://127.0.0.1:8080

The runwsgi commands takes a PasteDeploy configuration file as its
argument. You can configure different WSGI capable servers,
the WSGI pipeline or logging configuration in this file.

Now you are able to log in using a browser, as described in
`Logging In To Zope`_.


Running Zope as a Daemon
------------------------

Zope has no built-in support for running as a daemon any more. You can
use projects like supervisord to achieve this or use your operating
system's built-in process manager.


Debugging Zope
--------------

In order to debug the Zope application, it can be helpful to connect
to its database and inspect or change it on the command line. This
feature was previously available via the dedicated `zopectl debug`
command - in the new WSGI setup this is available via the `zconsole`
module and console script::

  $ bin/zconsole debug etc/wsgi.conf
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
---------------

This was previously availabe using `zopectl run <path_to_script> <scriparg1> ...`.
Again in the WSGI setup the `zconsole` module and console script can be used::

  $ bin/zconsole run etc/wsgi.conf <path_to_script> <scriptarg1> ...

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
the "make instance" process.

Now you're off and running! You should be looking at the Zope
management screen which is divided into two frames. On the left you
can navigate between Zope objects and on the right you can edit them
by selecting different management functions with the tabs at the top
of the frame.

To create content to be rendered at http://yourhost:8080/ create a `Page
Template` or `DTML Document` named ``index_html``.


Adding Users
------------

Adding users with full administrative access ("Managers")
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you need to add a Manager to an existing Zope instance, you can do
this using `addzope2user` as follows::

  $ bin/addzope2user user password

The script expects to find the configuration file at ``etc/wsgi.conf``.


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
home. The file has one line with a colon-separated login and password, like::

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
