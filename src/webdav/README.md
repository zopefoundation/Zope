WebDAV testing
==============

The WebDAV implementation in Zope was tested using the "litmus" tool (see
http://www.webdav.org/neon/litmus) to gauge its compatibility with the WebDAV
standard. This document contains notes about warnings or failures.

To run the test suite, download and build the `litmus` tool. You cannot run it
in place inside the sources folder, you need to run `make install` first so it
can find its libraries. This is a bug in `litmus` itself.

`litmus --help` will show the few available options. Provided you have your
Zope instance locally on port 8080, the following will run the complete test
suite:

`litmus -k http://localhost:8080/ <USER> <PASSWORD>`


Test run on 2020/02/01
----------------------
Litmus version 0.13, Zope version 5 pre-alpha, web server waitress 1.4.2.

The following lists all changes compared to the original test run from 2007. If
a test is not mentioned the results have not changed.

**'basic' tests**

- `4. put_get_utf8_segment`: PASS (non-ASCII object IDs are now allowed)
- results: 16 tests run: 16 passed, 0 failed. 100.0%

**'copymove' tests**

- results: 13 tests run: 13 passed, 0 failed. 100.0%

**'props' tests**

- `17. prophighunicode`: PASS (non-ASCII properties are now allowed)
- `18. propget`: PASS (because test 17 now sets the property successfully)
- results: 30 tests run: 30 passed, 0 failed. 100.0%

**'locks' tests**

- `15. cond_put`: PASS (the WebDAV code now sets ETag headers)
- `16. fail_cond_put`: FAIL (no longer skipped because ETags are present)

  Conditional PUT requests are no longer skipped, but invalid lock tokens
  or invalid conditional headers will now erroneously return a status of
  204 (no content) instead of failing. This affects the following tests:

  - `16. fail_cond_put`
  - `20. fail_complex_cond_put`

- `19. complex_cond_put`: PASS (the WebDAV code now sets ETag headers)
- `34. notowner_modify`: No longer WARNING for a bad status code for DELETE
- `36. indirect_refresh`: PASS
- results: 34 tests run: 28 passed, 6 failed. 82.4%

**'http' tests**

- `2. expect100`: PASS (no longer seeing any timeouts)
- results: 4 tests run: 4 passed, 0 failed. 100.0%


Test run on 2007/06/17
----------------------
Litmus version 0.10.5, Zope version (probably) 2.9.7, web server ZServer.

**'basic' tests**

- `4. put_get_utf8_segment`: FAIL (PUT of `/litmus/res-%e2%82%ac` failed:
  400 Bad Request)

  Zope considers the id `res-%e2%82%ac` invalid due to the
  `bad_id` regex in `OFS.ObjectManager`, which is consulted whenever
  a new object is added to a container through the OFS
  objectmanager interface.  It's likely possible to replace this
  regex with a more permissive one via a monkepatch as necessary.

- `8. delete_fragment`: WARNING: DELETE removed collection resource with
  Request-URI including fragment; unsafe `ZServer` strips off the fragment
  portion of the URL and throws it away, so we never get a chance to detect
  if a fragment was sent in the URL within appserver code.

**'props' tests**

- `17. prophighunicode`: FAIL (PROPPATCH of property with high
  unicode value)

  The exception raised by Zope here is:


        2007-06-17 15:27:02 ERROR Zope.SiteErrorLog http://localhost:8080/litmus/prop2/PROPPATCH
          Traceback (innermost last):
             Module ZPublisher.Publish, line 119, in publish
             Module ZPublisher.mapply, line 88, in mapply
             Module ZPublisher.Publish, line 42, in call_object
             Module webdav.Resource, line 315, in PROPPATCH
             Module webdav.davcmds, line 190, in __init__
             Module webdav.davcmds, line 226, in parse
             Module webdav.xmltools, line 98, in strval
           UnicodeEncodeError: 'latin-1' codec can't encode characters in position 0-1: ordinal not in range(256)

  This is because the `webdav.xmltools.Node.strval` method attempts
  to encode the string representation of the property node to the
  'default' propertysheet encoding, which is assumed to be
  'latin-1'.  The value of the received property cannot be encoded
  using this encoding.

- `18. propget`: FAIL (No value given for property
  {http://webdav.org/neon/litmus/}high-unicode)

  This is because test 17 fails to set a value.

**'locks' tests**

- `15. cond_put`: SKIPPED

  Zope does not appear to send an Etag in normal responses, which
  this test seems to require as a precondition for execution.  See
  http://www.mnot.net/cache_docs/ for more information about
  Etags.

  These tests appear to be skipped for the same reason:

  - `16. fail_cond_put`: SKIPPED
  - `19. complex_cond_put`: SKIPPED
  - `20. fail_complex_cond_put`: SKIPPED

  Zope's `OFS` package has an `OFS.EtagSupport.EtagSupport`
  class which is inherited by the `OFS.Lockable.LockableItem`
  class, which is in turn inherited by
  `OFS.SimpleItem.SimpleItem` (upon which almost all Zope content is
  based), so potentially all Zope content can reasonably easily
  generate meaningful ETags in responses.  Finding out why it's
  not generating them appears to be an archaeology exercise.

- `18. cond_put_corrupt_token`: FAIL (conditional PUT with invalid
  lock-token should fail: 204 No Content)

  I (chrism) haven't been able to fix this without breaking
  `32. lock_collection`, which is a more important interaction.  See
  `webdav.tests.testResource.TestResource.donttest_dav__simpleifhandler_cond_put_corrupt_token`.

- `22. fail_cond_put_unlocked`: FAIL (conditional PUT with invalid
  lock-token should fail: 204 No Content)

  I (chrism) haven't been able to fix this without breaking
  `32. lock_collection`, which is a more important interaction. See
  `webdav.tests.testResource.TestResource.donttest_dav__simpleifhandler_fail_cond_put_unlocked`.

- `23. lock_shared`: FAIL (LOCK on `/litmus/lockme`: 403 Forbidden)

  Zope does not support locking resources with lockscope 'shared'
  (only exclusive locks are supported for any kind of Zope
  resource).  Litmus could probably do a PROPFIND on the
  /litmus/lockme resource and check the <supportedlock> lockscope
  in the response before declaring this a failure (class 2 DAV
  servers are not required to support shared locks).

  The dependent tests below are skipped due to this failure:

  - `24. notowner_modify`: SKIPPED
  - `25. notowner_lock`: SKIPPED
  - `26. owner_modify`: SKIPPED
  - `27. double_sharedlock`: SKIPPED
  - `28. notowner_modify`: SKIPPED
  - `29. notowner_lock`: SKIPPED
  - `30. unlock`: SKIPPED

- `34. notowner_modify`: WARNING: DELETE failed with 412 not 423 FAIL
  (MOVE of locked resource should fail)

  Unknown reasons (not yet investigated).

- `36. indirect_refresh`: FAIL (indirect refresh LOCK on
  `/litmus/lockcoll/` via `/litmus/lockcoll/lockme.txt`: 400 Bad
  Request)

  Unknown reason (not yet investigated).

**'http' tests**

- `2. expect100`: FAIL (timeout waiting for interim response)

  Unknown reason (not yet investigated).

**additional notes**

litmus 0.11 times out on several of the lock tests due to some
HTTP-level miscommunication between neon 0.26 and Zope (perhaps, as
I've gathered on the litmus maillist, having to do with neon 0.26's
expectation to use persistent connections, and perhaps due to some
bug in Zope's implementation of same), and this is why litmus
0.11/neon 0.25 was used to do the testing even though litmus 11.0
was available.  litmus 0.10.5 times out in a similar fashion on the
"http.expect100" test but on none of the lock tests.

**analyses**

Analysis of what happens during locks `32. lock_collection`:

The first request in this test set is a successful LOCK request
with "Depth: infinity" to `/litmus/lockcoll` (an existing
newly-created collection):

        LOCK /litmus/lockcoll/ HTTP/1.1
        Depth: infinity

        <?xml version="1.0" encoding="utf-8"?>
        <lockinfo xmlns='DAV:'>
         <lockscope><exclusive/></lockscope>
         <locktype><write/></locktype>
         <owner>litmus test suite</owner>
        </lockinfo>

Zope responds to this with a success response like this:

        <?xml version="1.0" encoding="utf-8" ?>
        <d:prop xmlns:d="DAV:">
          <d:lockdiscovery>
            <d:activelock>
              <d:locktype><d:write/></d:locktype>
              <d:lockscope><d:exclusive/></d:lockscope>
              <d:depth>infinity</d:depth>
              <d:owner>litmus test suite</d:owner>
              <d:timeout>Second-3600</d:timeout>
              <d:locktoken>
              <d:href>opaquelocktoken:{olt}</d:href>
              </d:locktoken>
            </d:activelock>
          </d:lockdiscovery>
       </d:prop>

(`{olt}` in the above quoted response represents an actual valid
lock token, not a literal)

The next request sent during this test is a conditional PUT request to
`/litmus/lockcoll/lockme.txt` (which doesn't yet exist at the time of the
request):

        PUT /litmus/lockcoll/lockme.txt HTTP/1.1
        If: <http://localhost:8080/litmus/lockcoll/> (<opaquelocktoken:{olt})

The If header in this request specifies that the `{olt}` locktoken
should be checked against the resource
`http://localhost:8080/litmus/lockcoll/` (the collection parent).

In response to the PUT command, inside Zope, a `NullResource`
object is created representing `/litmus/lockcoll/lockme.txt`.
`NullResource.PUT` determines its parent is locked and so calls
`dav__simpleifhandler` on the parent (`/litmus/lockcoll`).  This
does not raise an exception due to the fact that the If header
specifies it as the resource being consulted for a lock.

With the "is the parent locked" guard condition satisfied,
`NullResource.PUT` continues. It extracts the file body out of the
request and creates a new object based on the file body content
using `PUT_factory`.  It then turns around and sets the new object
into its container and calls `newob.PUT(REQUEST, RESPONSE)`.

Litmus expects the PUT request to succeed with a 2XX response
(and presumably the new `lockme.txt` resource should be created
within `/litmus/lockcoll`).  See
http://mailman.webdav.org/pipermail/litmus/2005-August/000169.html
for more rationale about why this is assumed to be "the right thing".
