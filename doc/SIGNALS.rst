Signals (POSIX only)
====================

Signals are a POSIX inter-process communications mechanism.
If you are using Windows then this documentation does not apply.

Zope responds to signals which are sent to the process id
specified in the file '$INSTANCE_HOME/var/Z2.pid'::

    SIGHUP  - close open database connections, then restart the server
              process. A idiom for restarting a Zope server is:

              kill -HUP `cat $INSTANCE_HOME/var/z2.pid`

    SIGTERM - close open database connections then shut down. A common
              idiom for shutting down Zope is:

              kill -TERM `cat $INSTANCE_HOME/var/Z2.pid`

    SIGINT  - same as SIGTERM

    SIGUSR2 - close and re-open all Zope log files (z2.log, event log,
              detailed log.) A common idiom after rotating Zope log files
              is:

              kill -USR2 `cat $INSTANCE_HOME/var/z2.pid`

