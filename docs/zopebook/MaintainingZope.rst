Maintaining Zope
################

.. include:: includes/zope2_notice.rst

Keeping a Zope site running smoothly involves a number of administrative tasks.
This chapter covers some of these tasks, such as:

  - Starting Zope automatically at boot time
  - Installing new products
  - Setting parameters in the Control Panel
  - Monitoring
  - Cleaning up log files
  - Packing and backing up the database
  - Database recovery tools

Maintenance often is a very platform-specific task, and Zope runs on many
platforms, so you will find instructions for several different operating
systems here. It is not possible to provide specifics for every system;
instead, we will supply general instructions which should be modified according
to your specific needs and platform.

Starting Zope Automatically at Boot Time
========================================

For testing and developing purposes you will start Zope manually most of the
time, but for production systems it is necessary to start Zope automatically at
boot time. Also, we will want to shut down Zope in an orderly fashion when the
system goes down. We will describe the necessary steps for Microsoft Windows
and some Linux distributions. Take a look at the Linux section for other
Unix-like operating systems. Much of the information presented here also
applies to System V like Unices.

Debug Mode and Automatic Startup
++++++++++++++++++++++++++++++++

If you are planning to run Zope on a Unix production system you should also
disable *debug mode*. This means removing the `-D` option in startup scripts
(e.g. the `start` script created by Zope at installation time which calls z2.py
with the `-D` switch). In debug mode, Zope does not detach itself
from the terminal, which could cause startup scripts to malfunction.

On Windows, running Zope as a service disables debug mode by default. You still
can run Zope in debug mode by running Zope manually from a startup script with
the `-D` option.
Again, this is not recommended for production systems, since debug mode causes
performance loss.

Automatic Startup for Custom-Built Zopes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Even if you do not want to use the prepackaged Zope that comes with your
distribution it should be possible to re-use those startup scripts, eg. by
installing the prepackaged Zope and editing the appropriate files and symlinks
in `/etc/rc.d` or by extracting them with a tool like `rpm2cpio`.

In the following examples we assume you installed your custom Zope to a
system-wide directory, eg. `/usr/local/zope`. If this is not the case please
replace every occurence of `/usr/local/zope` below with your Zope installation
directory. There should also be a separate Zope system user present. Below we
assume that there is a user `zope`, group `nogroup` present on your system. The
user `zope` should of course have read access to the `$ZOPE_HOME` directory
(the directory which contains the "top-level" Zope software and the "z2.py"
script) and its descendants, and write access to the contents of the `var`
directory.

If you start Zope as root, which is usually the case when starting Zope
automatically on system boot, it is required that the `var` directory belongs
to root. Set the ownership by executing the command::

  chown root var

as root.

To set up a Zope binary package with built-in python situated in::
/usr/local/zope running as user `zope` , with a "WebDAV Source port" set to
8081, you would set::

  ZOPE_HOME=/usr/local/zope
  PYTHON_BIN=$ZOPE_HOME/bin/python
  COMMON_PARAMS="-u zope -z $ZOPE_HOME -Z /var/run/zope.pid -l /var/log/Z2.log -W 8081"

You can also set up a file `/etc/sysconfig/zope` with variable
ZOPE_HTTP_PORT::

  ZOPE_HTTP_PORT=80

to set the HTTP port. The default is to start them at port 8080 and
8021.

Unfortunately, all Linux distributions start and stop services a little
differently, so it is not possible to write a startup script that integrates
well with every distribution. We will try to outline a crude version of a
generic startup script which you can refine according to your needs.

To do this some shell scripting knowledge and root system access is required.

Linux startup scripts usually reside in::

  /etc/init.d

or in::

  /etc/rc.d/init.d

For our examples we assume the startup scripts to be in::

  /etc/rc.d/init.d

adjust if necessary.

To let the boot process call a startup script, you also have to place a
symbolic link to the startup script in the::

  /etc/rc.d/rc?.d

directories, where `?` is a number from 0-6 which stands for the SystemV run
levels. You usually will want to start Zope in run levels 3 and 5 (3 is full
multi-user mode, 5 is multiuser mode with X started, according to the `"Linux
Standard Base" <https://wiki.linuxfoundation.org/lsb/start>`_,
so you would place two links in the
/etc/rc.d' directories. Be warned that some systems (such as Debian) assume
that runlevel 2 is full multiuser mode. As stated above, we assume the main
startup script to located in::

  /etc/rc.d/init.d/zope

if your system puts the::

  init.d

directory somewhere else, you should accomodate the paths below::

  # cd /etc/rc.d/rc3.d
  # ln -s /etc/rc.d/init.d/zope S99zope
  # cd /etc/rc.d/rc5.d
  # ln -s /etc/rc.d/init.d/zope S99zope

The scripts are called by the boot process with an argument::

  start

when starting up and::

  stop

on shutdown.

A simple generic startup script structure could be something like this::

  #!/bin/sh

  # set paths and startup options
  ZOPE_HOME=/usr/local/zope
  PYTHON_BIN=$ZOPE_HOME/bin/python
  ZOPE_OPTS=" -u zope -P 8000"
  EVENT_LOG_FILE=$ZOPE_HOME/var/event.log
  EVENT_LOG_SEVERITY=-300
  # define more environment variables ...

  export EVENT_LOG_FILE  EVENT_LOG_SEVERITY
  # export more environment variables ...

  umask 077
  cd $ZOPE_HOME

  case "$1" in 

  start)
  # start service
  exec $PYTHON_BIN $ZOPE_HOME/z2.py $ZOPE_OPTS

  # if you want to start in debug mode (not recommended for
  # production systems):
  # exec $PYTHON_BIN $ZOPE_HOME/z2.py $ZOPE_OPTS -D &
  ;;
  stop)
  # stop service
  kill `cat $ZOPE_HOME/var/Z2.pid`
  ;;
  restart)
  # stop service and restart
  $0 stop
  $0 start
  ;;            
  *)
  echo "Usage: $0 {start|stop|restart}"
  exit 1
  ;;
  esac

This script lets you perform start / stop / restart operations:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

start
  Start Zope (and the zdaemon management process)

stop
  Stop Zope. Kill Zope and the zdaemon management process

restart
  Stop then start Zope

MS Windows
++++++++++

The prevalent way to autostart Zope on MS Windows is to install
Zope as a service.

If you installed Zope on Windows NT/2000/XP to be started manually and later on
want it started as a service, perform these steps from the command line to
register Zope as a Windows service:::

  > cd c:\Program Files\zope
  > bin\lib\win32\PythonService.exe /register 
  > bin\python.exe ZServer\ZService.py --startup auto install

Replace::

  c:\Program Files\zope

with the path to your Zope installation. Zope should now be installed as a
service which starts automatically on system boot. To start and stop Zope
manually, go to the Windows service administration tool, right-click the Zope
service and select the corresponding entry.

Installing New Products
=======================

Zope is a framework for building websites from new and existing software, known
as Zope *products*. A product is a Python package with special conventions that
register with the Zope framework. The primary purpose of a Zope product is to
create new kinds of objects that appear in the add list. This extensibility
through products has spawned a broad market of add-on software for Zope.

The guidelines for packaging a product are given in the "Packaging Products"
section in the `Zope Products chapter of the Zope Developer Guide
<https://zope.readthedocs.io/en/latest/zdgbook/Products.html>`_.
However, since these guidelines are not
enforced, many Zope products adhere to different conventions. This section will
discuss the different approaches to installing Zope packages.

To install a Zope product, you first download an archive file from a website,
such as the `Downloads section <https://old.zope.dev/Products/>`_ of
old.zope.dev.
These archive files come in several varieties, such as tgz (gzipped tar files)
zip (the popular ZIP format common on Windows), and others.

In general, unpacking these archives will create a subdirectory containing the
Product itself. For instance, the::

  Poll-1.0.tgz

archive file in the "Packaging Products" section mentioned above contains a
subdirectory of `Poll`. All the software is contained in this directory.

To install the product, you unarchive the file in the::

  lib/python/Products

directory. In the Poll example, this will create a directory::

  lib/python/Products/Poll

Unfortunately not all Zope developers adhere to this convention. Often the
archive file will have the::

  lib/python/Products

part of the path included. Worse, the archive might contain no directory, and
instead have all the files in the top-level of the archive. Thus, it is advised
to inspect the contents of the archive first.

Once you have the new directory in::

  lib/python/Products

you need to tell Zope that a new product has been added. You can do this by
restarting your Zope server through the Control Panel of the Zope Management
Interface (ZMI), or, on POSIX systems, by sending the Zope process a::

  -HUP

signal. For instance, from the Zope directory:::

  kill -HUP `cat var/Z2.pid`

If your Zope server is running in debug mode, a log message will appear
indicating a new product has been discovered and registered.

To confirm that your product is installed, log into your Zope site and visit
the Control Panel's Products section. You should see the new product appear in
the list of installed products.

If there was a problem with the installation, the Control Panel will list it as
a "Broken Product". Usually this is because Python had a problem importing a
package, or the software had a syntax error. You can visit the broken product
in the Control Panel and click on its *Traceback* tab. You will see the Python
traceback generated when the package was imported.

A traceback generally will tell you what went wrong with the import. For
instance, a package the software depends on could be missing. To illustrate
this take a look at the traceback below - a result of trying to install
`CMFOODocument <https://old.zope.dev/Members/longsleep/CMFOODocument>`_ without
the (required) CMF package:::

  Traceback (most recent call last):
  File "/usr/share/zope/2.6.0/lib/python/OFS/Application.py", line 541, in import_product
  product=__import__(pname, global_dict, global_dict, silly)
  File "/usr/share/zope/2.6.0/lib/python/Products/CMFOODocument/__init__.py", line 19, in ?
  import OODocument
  File "/usr/share/zope/2.6.0/lib/python/Products/CMFOODocument/OODocument.py", line 31, in ?
  from Products.CMFCore.PortalContent import NoWL, ResourceLockedError
  ImportError: No module named CMFCore.PortalContent

Server Settings
===============

The Zope server has a number of settings that can be adjusted for performance.
Unfortunately, performance tuning is not an exact science, that is, there is no
recipe for setting parameters. Rather, you have to test every change. To load
test a site, you should run a test setup with easily reproducible results. Load
test a few significant spots in your application. The trick is to identify
typical situations while still permitting automated testing. There are several
tools to load test websites. One of the simple yet surprisingly useful tools
is::

  ab

which comes with Apache distributions. With `ab` you can test individual URLs,
optionally providing cookies and POST data. Other tools often allow one to
create or record a user session and playing it back multiple times. See eg. the
`Open System Testing Architecture <http://opensta.org>`_ or `JMeter
<https://jmeter.apache.org/>`_.

Database Cache
++++++++++++++

The most important is the database cache setting. To adjust these settings,
visit the Control Panel and click on the *Database* link.

There are usually seven database connections to the internal Zope database (see
*Database Connections* below for information about how to change the number of
connections). Each connection gets its own database cache. The "Target number
of objects in memory per cache" setting controls just that - the system will
try not to put more than this number of persistent Zope objects into RAM per
database connection. So if this number is set to 400 and there are seven
database connections configured, there should not be more than 2800 objects
sitting in memory. Obviously, this does not say much about memory consumption,
since the objects might be anything in size - from a few hundred bytes upwards.
The cache favors commonly used objects - it wholly depends on your application
and the kind of objects which memory consumption will result from the number
set here. As a rule, Zope objects are about as big as the data they contain.
There is only little overhead in wrapping data into Zope objects.

ZServer Threads
+++++++++++++++

This number determines how many ZServer threads Zope starts to service
requests. The default number is four (4). You may try to increase this number
if you are running a heavily loaded website. If you want to increase this to
more than seven (7) threads, you also should increase the number of database
connections (see the next section).

Database Connections
++++++++++++++++++++

We briefly mentioned Zope's internal database connections in the *Database
Cache* section above. Out of the box, the number of database connections is
hardwired to seven (7); but this can be changed. There is no "knob" to change
this number so in order to change the number of database connections, you will
need to enter quite deep into the systems' bowels. It is probably a wise idea
to back up your Zope installation before following any of the instructions
below.

Each database connection maintains its own cache (see above, "Database Cache"),
so bumping the number of connections up increases memory requirements. Only
change this setting if you're sure you have the memory to spare.

To change this setting, create a file called "custom_zodb.py" in your Zope
installation directory. In this file, put the following code::

  import ZODB.FileStorage
  import ZODB.DB

  filename = os.path.join(INSTANCE_HOME, 'var', 'Data.fs')
  Storage = ZODB.FileStorage.FileStorage(filename)
  DB = ZODB.DB(Storage, pool_size=25, cache_size=2000)

This only applies if you are using the standard Zope FileStorage storage.

The "pool_size" parameter is the number of database connections. Note that the
number of database connections should always be higher than the number of
ZServer threads by a few (it doesn't make sense to have fewer database
connections than threads). See above on how to change the number of ZServer
threads.


Monitoring
==========

To detect problems (both present and future) when running Zope on production
systems, it is wise to watch a few parameters.

Monitor the Event Log and the Access Log
++++++++++++++++++++++++++++++++++++++++

If you set the EVENT_LOG_FILE (formerly known as the STUPID_LOG_FILE) as an
environment variable or a parameter to the startup script, you can find
potential problems logged to the file set there. Each log entry is tagged with
a severity level, ranging from TRACE (lowest) to PANIC (highest). You can set
the verbosity of the event log with the environment variable
EVENT_LOG_SEVERITY. You have to set this to an integer value - see below::

  TRACE=-300   -- Trace messages

  DEBUG=-200   -- Debugging messages

  BLATHER=-100 -- Somebody shut this app up.

  INFO=0       -- For things like startup and shutdown.

  PROBLEM=100  -- This isn't causing any immediate problems, but deserves
                  attention.

  WARNING=100  -- A wishy-washy alias for PROBLEM.

  ERROR=200    -- This is going to have adverse effects.

  PANIC=300    -- We're dead!

So, for example setting EVENT_LOG_SEVERITY=-300 should give you all log
messages for Zope and Zope applications that use Zopes' logging system.

You also should look at your access log (usually placed in
$ZOPE_HOME/var/Z2.log). The Z2.log file is recorded in the `Common Log Format
<https://www.w3.org/Daemon/User/Config/Logging.html#common-logfile-format>`_.
The sixth field of each line contains the HTTP status code. Look out for status
codes of 5xx, server error. Server errors often point to performance problems.

Monitor the HTTP Service
++++++++++++++++++++++++

You can find several tools on the net which facilitate monitoring of remote
services, for example `Nagios <https://www.nagios.org/>`_.

For a simple "ping" type of HTTP monitoring, you could also try to put a small
DTML Method with a known value on your server, for instance only containing the
character "1". Then, using something along the line of the shell script below,
you could periodically request the URL of this DTML Method, and mail an error
report if we are getting some other value (note the script below requires a
Un*x-like operating system)::

  #!/bin/sh

  # configure the values below
  URL="http://localhost/ping"
  EXPECTED_ANSWER="1"
  MAILTO="your.mailaddress@domain.name"
  SUBJECT="There seems to be a problem with your website"
  MAIL_BIN="/bin/mail"

  resp=`wget -O - -q -t 1 -T 1 $URL`
  if [ "$resp" != "$EXPECTED_ANSWER" ]; then
  $MAIL_BIN -s "$SUBJECT" $MAILTO <<EOF
  The URL 
  ----------------------------------------------
  $URL 
  ----------------------------------------------
  did not respond with the expected value of $EXPECTED_ANSWER. 
  EOF
  fi;

Run this script eg. every 10 minutes from cron and you should be set for simple
tasks. Be aware though that we do not handle connections timeouts well here. If
the connection hangs, for instance because of firewall misconfiguration `wget`
will likely wait for quite a while (around 15 minutes) before it reports an
error.

Log Files
=========

There are two main sources of log information in Zope, the access log and the
event log.

Access Log
++++++++++

The access log records every request made to the HTTP server. It is recorded in
the `Common Log Format
<https://www.w3.org/Daemon/User/Config/Logging.html#common-logfile-format>`_.

The default target of the access log is the file $ZOPE_HOME/var/Z2.log. Under
Unix it is however possible to direct this to the syslog by setting the
environment variable ZSYSLOG_ACCESS to the desired domain socket (usually
`/dev/log`)

If you are using syslog, you can also set a facility name by setting the
environment variable ZSYSLOG_FACILITY. It is also possible to log to a remote
machine. This is also controlled, you might have guessed it, by an environment
variable. The variable is called ZSYSLOG_SERVER and should be set to a string
of the form "host:port" where host is the remote logging machine name or IP
address and port is the port number the syslog daemon is listening on (usually
514).

Event Log
+++++++++

The event log (formerly also called "stupid log") logs Zope and third-party
application message. The ordinary log method is to log to a file specified by
the EVENT_LOG_FILE, eg. `EVENT_LOG_FILE=$ZOPE_HOME/var/event.log`.

On Unix it is also possible to use the syslog daemon by setting the environment
variable ZSYSLOG to the desired Unix domain socket, usually `/dev/log` . Like
with access logs (see above), it is possible to set a facility name by setting
the ZSYSLOG_FACILITY environment variable, and to log to a remote logging
machine by setting the ZSYSLOG_SERVER variable to a string of the form
"host:port", where port usually should be 514.

You can coarsely control how much logging information you want to get by
setting the variable EVENT_LOG_SEVERITY to an integer number - see the section
"Monitor the Event Log and the Access Log" above.

Log Rotation
++++++++++++

Log files always grow, so it is customary to periodically rotate logs. This
means logfiles are copied, optionally compressed, and the current logfile
is truncated. On Unix, there is the `logrotate` package which traditionally
handles this. A sample configuration might look like this::

  /usr/local/zope/var/Z2.log {
  rotate 25
  weekly
  copytruncate
  compress
  }

This would tell logrotate to handle Zopes access log file, keep 25 rotated log
files and do a log rotation every week. After the old log file has been saved
it will be compressed. See the documentation to `logrotate` for further details.

On Windows there are no widespread tools for log rotation. You might try the
`KiWi Syslog Daemon <https://www.kiwisyslog.com>`_ and configure Zope to log to
it. Also see the sections "Access Log" and "Event Log" above.

Packing and Backing Up the FileStorage Database
===============================================

The storage used by default by Zope's built-in object database, FileStorage, is
an undoable storage. This essentially means changes to Zope objects do not
overwrite the old object data, rather the new object gets appended to the
database. This makes it possible to recreate an objects previous state, but it
also means that the file the objects are kept in (which usually resides in
$ZOPE_HOME/var/Data.fs) always keeps growing.

To get rid of obsolete objects, you need to:: `pack` the ZODB. This can be done
manually by opening Zopes Control_Panel and clicking on the "Database
Management" link. Zope offers you the option of removing only object version
older than an adjustable amount of days.

Zope backup is quite straightforward. If you are using the default storage
(FileStorage), all you need to do is to save the file::

  $ZOPE_HOME/var/Data.fs

This can be done online, because Zope only appends to the `Data.fs` file - and
if a few bytes are missing at the end of the file due to a copy while the file
is being written to, ZODB is usually capable of repairing that upon startup.
The only thing to worry about would be if someone were to be using the *Undo*
feature during backup. If you cannot ensure that this does not happen, you
should take one of two routes. The first is be to shutdown Zope prior to a
backup, and the second is to do a packing operation in combination with backup.
Packing the ZODB leaves a file `Data.fs.old` with the previous contents of the
ZODB. Since Zope does not write to that file anymore after packing, it is safe
to backup this file even if undo operations are performed on the live ZODB.

To backup `Data.fs` on Linux, you should not `tar` it directly, because `tar`
will exit with an error if files change in the middle of a `tar` operation.
Simply copying it over first will do the trick.

Database Recovery Tools
=======================

To recover data from corrupted ZODB database file (typically located in
`$ZOPE_HOME/var/Data.fs` ) there is a script `fsrecover.py` located in
$ZOPE_HOME/lib/python/ZODB.

fsrecover.py has the following help output::

  python fsrecover.py [ <options> ] inputfile outputfile

  Options:

  -f -- force output even if output file exists

  -v level -- Set the 
  verbosity level:

  0 -- Show progress indicator (default)

  1 -- Show transaction times and sizes

  2 -- Show transaction times and sizes, and
  show object (record) ids, versions, and sizes.

  -p -- Copy partial transactions. If a data record in the middle of a
  transaction is bad, the data up to the bad data are packed. The
  output record is marked as packed. If this option is not used,
  transaction with any bad data are skipped.

  -P t -- Pack data to t seconds in the past. Note that is the "-p"
  option is used, then t should be 0.        
