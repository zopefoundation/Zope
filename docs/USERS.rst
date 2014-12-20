Special Users
=============

Because Zope is managed through the web, user names and passwords must be
used to assure that only authorized people can make changes to a Zope
installation.

Adding Managers
---------------

If you need to add a Manager to an existing Zope instance, you can do
this using `zopectl` as follows::

  zopectl adduser `name` `password`

The Initial User
----------------

An initial username and password is needed to "bootstrap" the creation of
normal managers of your Zope site.  This is accomplished through the
use of the 'inituser' file in the directory specified as the instance
home. 

The first time Zope starts, it will detect
that no users have been defined in the root user folder.  It will search
for the 'inituser' file and, if it exists, will add the user defined
in the file to the root user folder.

Normally, 'inituser' is created by the Zope install scripts.  Either
the installer prompts for the password or a randomly generated
password is created and displayed at the end of the build script.

You can use the 'zpasswd.py' script to create 'inituser' yourself.
Execute 'zpasswd.py' like this::

    python zpasswd.py inituser

The script will prompt you for the name, password, and allowed
domains.  The default is to encode the password with SHA, so please
remember this password as there is no way to recover it (although
'zpasswd.py' lets you reset it.)

The Emergency User
------------------

In some situations you may need to bypass normal security controls
because you have lost your password or because the security settings
have been mixed up.  Zope provides a facility called an "emergency
user" so that you can reset passwords and correct security
settings.

The emergency user password must be defined outside the application
user interface.  It is defined in the 'access' file located
in the Zope directory.  It should be readable only by the user
as which your web server runs.

To create the emergency user, use 'zpasswd.py' to create the
'access' file like this::

    python zpasswd.py access

In order to provide a somewhat higher level of security, various
encoding schemes are supported which provide access to either SHA-1
encryption or the standard UNIX crypt facility if it has been compiled
into Python.  Unless you have some special requirements (see below), 
you should use the SHA-1 facility, which is the default.

Format of 'inituser' and 'access'
---------------------------------

A password file should consist of a single line of the form::

    name:password

Note that you may also add an optional third component to the line in the
access file to restrict access by domain.  For example, the line::

    mario:nintendoRules:*.mydomain.com

in your 'access' file will only allow permit emergency user access
from `*.mydomain.com` machines. Attempts to access the system from
other domains will fail, even if the correct emergency user name
and password are used.

Please note that if you use the ZServer monitor capability, you will
need to run with a clear text password.
