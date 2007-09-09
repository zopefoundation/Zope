MailHost


  The MailHost product provides support for sending email from
  within the Zope environment using MailHost objects.

  Email can optionally be encoded using Base64, Quoted-Printable
  or UUEncode encoding.

  MailHost provides integration with the Zope transaction system and optional
  support for asynchronous mail delivery. Asynchronous mail delivery is
  implemented using a queue and a dedicated thread processing the queue. The
  thread is (re)-started automatically when sending an email. The thread can be
  startet manually (in case of restart) by calling its
  manage_restartQueueThread?action=start method through HTTP. There is
  currently no possibility to start the thread at Zope startup time.

  Supports TLS/SSL encryption (requires Python compiled with SSL support)
