MailHost


  The MailHost product provides support for sending email from
  within the Zope environment using MailHost objects.

  An optional character set can be specified to automatically encode unicode
  input, and perform appropriate RFC 2822 header and body encoding for
  the specified character set.  Full python email.Message.Message objects
  may be sent.

  Email can optionally be encoded using Base64, Quoted-Printable
  or UUEncode encoding (though automatic body encoding will be applied if a
  character set is specified).

  MailHost provides integration with the Zope transaction system and optional
  support for asynchronous mail delivery. Asynchronous mail delivery is
  implemented using a queue and a dedicated thread processing the queue. The
  thread is (re)-started automatically when sending an email. The thread can be
  startet manually (in case of restart) by calling its
  manage_restartQueueThread?action=start method through HTTP. There is
  currently no possibility to start the thread at Zope startup time.

  Supports TLS/SSL encryption (requires Python compiled with SSL support)
