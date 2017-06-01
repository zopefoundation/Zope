Configuring and Running Zope
============================

.. highlight:: bash


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

In order to enable debug mode, you can add the additional `-d` or
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
command and the same can be achieved in the new WSGI setup.

Assuming you have a Python interpreter with the correct sys.path
available, for example as ``bin/zopepy``, you can run::

  $ ZOPE_CONFIG=etc/wsgi.conf bin/zopepy
  >>> import Zope2
  >>> app = Zope2.app()
  >>> app
  <Application at >

  >>> app.acl_users
  <UserFolder at /acl_users>

  >>> import transaction
  >>> transaction.begin()
  >>> app.acl_users._doAddUser('foo', 'bar', ['Manager'], [])
  <User 'foo'>
  >>> transaction.commit()


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


Troubleshooting
---------------

- This version of Zope requires Python 2.7 or Python 3.4 and later.
  It will *not* run with any version of PyPy.

- To build Python extensions you need to have Python configuration
  information available. If your Python comes from an RPM you may
  need the python-devel (or python-dev) package installed too. If
  you built Python from source all the configuration information
  should already be available.

- See the :doc:`changes` for important notes on this version of Zope.
