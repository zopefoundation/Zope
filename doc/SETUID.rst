Zope effective user support
===========================

.. note:: 
  It is best practice to run Zope behind a reverse proxy like
  Apache, Squid or Varnish. In this case, you do not need to run
  or install Zope with root privileges, since the reverse proxy
  will bind to port 80 and proxy back all request to Zope running
  on an unpriviledged port.

Zope can bind its network service to low ports such as 21 (FTP) and
80 (HTTP).  In order to bind to low ports, Zope must be started as
the root user.  However, Zope will only run as root long enough to
bind to these low ports.  It will then attempt to setuid to a less
privileged user.

You must specify the user to which Zope will attempt to setuid by
changing the 'effective-user' parameter in the zope.conf
configuration file to an existing username or UID.  All runtime
files will be written as this user.  If you do not specify an
'effective-user' in the configuration file, and you attempt to start
Zope, it will refuse to start.

Zope additionally emits a warning if you specify 'nobody' as the
'effective-user'.  The rationale for this warning stems from the
fact that, historically, many other UNIX services dropped privileges
to the 'nobody' account after starting as root.  Any security
defects in these services could cause someone to gain access as the
'nobody' account on your system.  If someone was to gain control of
your 'nobody' account they could compromise your Zope files.

The most important thing to remember about effective user support is
that you don't have to start Zope as root unless you want to listen
for requests on low ports (ports beneath 1024).  In fact, if you
don't have this need, you are much better off just starting Zope
under a dedicated user account.

