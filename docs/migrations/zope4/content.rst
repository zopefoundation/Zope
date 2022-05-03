.. _zope4contentmigration:

Migrating content
=================
These issues may appear when rendering content (templates, scripts or
other built-in Zope code objects) created with Zope 2 in Zope 4.


.. _zope4pagetemplatemigration:

Page Template parsing issues
----------------------------
Zope 4 is using `Chameleon <https://chameleon.readthedocs.io>`_ as its new
parsing engine for Page Templates. Chameleon is strict. **Very strict**. Have I
mentioned that Chameleon's parsing is **extremely strict**? It will throw any
sloppy HTML and TAL/TALES right in your face and refuse to compile it, even if
it may be syntactically correct and the Zope 2 parsing engine has worked with
it just fine.

- namespace names are case-sensitive. For Page templates, that means only
  lowercased namespaces like ``tal`` or ``metal`` are allowed:

  .. code-block:: html

     <span TAL:CONTENT="string:foo"></span>  <!-- BAD namespace TAL -->
     <span Tal:content="string:foo"></span>  <!-- BAD namespace Tal -->
     <span tal:content="string:foo"></span>  <!-- OK -->

- Opening and closing tags must match in type:

  .. code-block:: html

     <tr>
       <td>...</td>
     </td>           <!-- BAD: Mismatched open/close tag -->

- Opening and closing tags must match in case:

  .. code-block:: html

     <a href=".">Text</A>  <!-- BAD: Mismatched open/close tag -->
     <a href=".">Text</a>  <!-- OK -->
     <A href=".">Text</A>  <!-- OK -->
     <Td>...</td>          <!-- BAD: Mismatched open/close tag -->
     <td>...</td>          <!-- OK -->

- HTML comments must not contain any double hyphens inside the comment or more
  than two hyphens in the closing sequence:

  .. code-block:: html

    <!-- OK -->
    <!--- OK -->
    <!--  BAD -- BAD -->
    <!--  BAD <span tal:replace="string:----"/> -->
    <!-- BAD --->

- HTML syntax errors that were ignored before

   .. code-block:: sh

    <a href="." " class="mystyle">...</a>  <!-- BAD: extraneous " -->

- Python expression syntax errors that were parsing OK under Zope 2 but caused
  errors at execution time are now caught during parsing:

   .. code-block:: html

    <a href="" 
       tal:attributes="href python:context.myfunc(a=1, a=1)">
      ...
    </a>  <!-- BAD: Python syntax error>

To help identify such issues, code for a `External Method` that searches the
ZODB for Page Templates and reveals errors has been provided. Make sure you
have the ``Products.ExternalMethod`` egg in your application configuration
before following these steps:

- In the ZMI root, instantiate a `External Method` object from the dropdown at
  the top right.

- Give it an id of your choosing and an optional title. For `Module Name` enter
  ``Products.PageTemplates.find_bad_templates``, and for `Function Name`
  ``find_bad_templates``. Click on `Save Changes`.

- Visit the `Test` tab at the top. The process time will vary with the size of
  your ZODB object tree and the number of Page Templates found. The report page
  will identify each Page Template that does not compile cleany and point out
  the issues.

Run the script after each round of fixes as the parser will stop after the
first error it encounters, even if there are more errors in a template.
