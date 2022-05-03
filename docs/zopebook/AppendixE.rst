Appendix E: DTML Name Lookup Rules
##################################

.. include:: includes/zope2_notice.rst

These are the rules which DTML uses to resolve names mentioned in `name=` and
`expr=` tags. The rules are in order from first to last in the search path.

The DTML call signature is as follows::

  def __call__(client=None, mapping={}, **kw)

The `client` argument is typically unreferenced in the body of DTML text, but
typically resolves to the "context" in which the method was called (for
example, in the simplest case, its client is the folder in which it lives).

The `mapping` argument is typically referred to as `_` in the body of DTML
text.

The keyword arguments (i.e. `**kw` ) are referred to by their respective names
in the body of DTML text.

1. The keyword arguments are searched.

2. The mapping object is searched.

3. Attributes of the client, including inherited and acquired attributes, are
   searched.

4. If DTML is used in a Zope DTML Method or Document object and the variable
   name is `document_id` or `document_title`, then the id or title of the
   document or method is used.

5. Attributes of the folder containing the DTML object (its container) are
   searched. Attributes include objects in the contents of the folder,
   properties of the folder, and other attributes defined by Zope, such as
   `ZopeTime`. Folder attributes include the attributes of folders containing
   the folder, with contained folders taking precedence over containing
   folders.

6. User-defined Web-request variables (ie. in the REQUEST.other namespace) are
   searched.

7. Form-defined Web-request variables (ie. in the REQUEST.form namespace) are
   searched.

8. Cookie-defined Web-request variables (ie. in the REQUEST.cookies namespace)
   are searched.

9. CGI-defined Web-request variables (ie. in the REQUEST.environ namespace) are
   searched.
