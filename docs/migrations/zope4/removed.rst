Zope products that are now distributed separately
=================================================
During the Zope 4 development, several packages that used to be included
have been separated out and ship separately.

On this page the term "add to your application buildout" is used generically.
How you do so depends on your chosen installation method, like adding an egg
name to a `requirements file` for ``pip`` installs, or adding it to an ``eggs``
specification for ``zc.buildout``.


ZServer
-------
ZServer does not support Python 3. The following only applies for Zope 4 under
Python 2.

If you want to continue using ZServer instead of moving to WSGI you need to add
the ZServer egg to your application buildout.

If you use the recipe ``plone.recipe.zope2instance`` in a buildout, add it to
its ``eggs`` attribute and also add the flag ``wsgi = off``.


Sessioning
----------
If you have used (or want to use) the built-in support for sessioning, add the
egg ``Products.Sessions`` to your application buildout, which provides the
basic infrastructure without the actual session data storage.

For non-production environments you can use the old
``Products.TemporaryFolder`` temporary folder solution for storing session
data. But this implementation is known to randomly lose session data, so do not
use it in production. Add the package ``Products.TemporaryFolder`` to your
application buildout and make sure your Zope configuration file contains a ZODB
configuration for a temporary folder like this::

  <zodb_db temporary>
      <mappingstorage>
        name Temporary database (for sessions)
      </mappingstorage>
      mount-point /temp_folder
      container-class Products.TemporaryFolder.TemporaryContainer
  </zodb_db>

If sessions are used very sparingly you can even get away with just adding a
Folder object named ``temp_folder`` at the root of the ZODB and restarting
Zope so the necessary ZODB objects for session support are created. This will
not lose session data, but it has a high risk of producing ZODB conflict errors
when storing data unless the session is used very carefully to minimize write
activity.
  
For production deployments see, see `the Zope book chapter on sessioning
for alternative session storage options
<https://zope.readthedocs.io/en/latest/zopebook/Sessions.html#alternative-server-side-session-backends-for-zope-4>`_.


External Methods
----------------
If you have External Method objects in your ZODB, make sure to add the egg
``Products.ExternalMethod`` to your application buildout.


Site Error Log
--------------
If you have used the Site Error Log (the ``error_logs`` objects that show
information about errors occurring in your application), add the egg
``Products.SiteErrorLog`` to your application buildout.
