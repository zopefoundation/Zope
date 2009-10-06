Filesytem Permissions
=====================

You need to set permissions on the directory Zope uses to store its
data. This will normally be the `var` directory in the instance home.
Zope needs to read and write data to this directory. Before
running Zope you should ensure that you give adequate permissions
to this directory for the userid Zope will run under.

Depending on how you choose to run Zope you will need to give
different permissions to the directory.  If you use Zope with an
existing web server, it will probably run Zope as 'nobody'. In this
case 'nobody' needs read and write permissions to the var directory.

If you change the way you run Zope, you may need to modify the permissions
of the directory and the files in it to allow Zope to read and write
under its changed userid.

