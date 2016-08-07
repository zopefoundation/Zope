Special Users
=============

Because Zope is managed through the web, user names and passwords must be
used to assure that only authorized people can make changes to a Zope
installation.


Adding Managers
---------------

If you need to add a Manager to an existing Zope instance, you can do
this using `addzope2user` as follows::

  $ bin/addzope2user user password

The script expects to find the configuration file at ``etc/wsgi.conf``.


The Initial User
----------------

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
