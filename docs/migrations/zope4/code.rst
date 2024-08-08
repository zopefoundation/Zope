.. _zope4codemigration:

Migrating Zope product code
===========================
The following list shows a few common migration issues independent of the
Python version used.


Changed import paths
--------------------
Several commonly used Zope code modules have moved. Here's a short list of
corrections you will have to make in your code. Many of these changed paths
have already existed under Zope 2, so you can make those corrections ahead of
time.

.. code-block:: python

   from Globals import InitializeClass  # OLD
   from AccessControl.class_init import InitializeClass  # NEW


``implementer`` versus ``implements``
-------------------------------------
How to signal that a class implements a specific interface has moved from a
function called at class level into a class decorator and changed its name:

.. code-block:: python

   from zope.interface import implementer
   from zope.interface import implements
   from .interfaces import IMyClass

   class MyClass:
       implements(IMyClass)  # OLD
       ...

   @implementer(IMyClass)  # NEW
   class AnotherClass:
       ...


.. _ZMI-label:

Migrating to the new bootstrap-based ZMI
----------------------------------------
Since Zope 4.0b6 the ZMI is styled using Bootstrap. The previously used
GIF icons were replaced by font glyphs which are stored in the package
`zmi.styles`_ (part of Zope) together with the CSS and JavaScript needed
by Bootstrap.

The free Font Awesome glyphs are used as icons, see the table of
`available icons`_.

Update existing package code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you have a Product or package which contains types, which can be added via
the ZMI, the default icon will be shown.

To use one of the new icons add an attribute named ``zmi_icon`` to the class.
As value use a name listed on `available icons`_ prefixed by ``fas fa-``.
Example to use the info icon (i in a circle)::

    zmi_icon = 'fas fa-info-circle'

A few Zope products provide content that can be added in the ZMI without
showing a dialog to collect data such as an id or title. These will now
default to showing the new modal dialog as well. You can prevent that by
adding another class variable::

    zmi_show_add_dialog = False

.. _`zmi.styles` : https://github.com/zopefoundation/Zope/tree/master/src/zmi/styles
.. _`available icons` : https://fontawesome.com/icons?d=gallery&m=free

Custom icons and resources
~~~~~~~~~~~~~~~~~~~~~~~~~~
To use custom icons (which are not part of `zmi.styles`) or load custom
CSS resp. JavaScript, you have to:

1. create a directory and fill it with your assets
2. register this directory as resource directory
3. register a subscription adapter for :class:`App.interfaces.ICSSPaths` resp.
   :class:`App.interfaces.IJSPaths`. This adapter has to return an iterable of
   paths resp. URLs which should be loaded when rendering the ZMI.

Example taken from `zmi.styles`_:

* Register the resource directory via ZCML:

  .. code-block:: XML

      <browser:resourceDirectory
          name="zmi"
          directory="resources" />

* Create a subscription adapter returning the path to the CSS file
  (`zmi.styles`_ has this code in `subscriber.py`.):


  .. code-block:: Python

      import zope.component
      import zope.interface


      @zope.component.adapter(zope.interface.Interface)
      def css_paths(context):
          """Return paths to CSS files needed for the Zope 4 ZMI."""
          return (
              '/++resource++zmi/bootstrap-4.1.1/bootstrap.min.css',
              '/++resource++zmi/fontawesome-free-5.1.0/css/all.css',
              '/++resource++zmi/zmi_base.css',
          )

* Register the subscriber via ZCML:

  .. code-block:: XML

      <subscriber
          provides="App.interfaces.ICSSPaths"
          factory=".subscriber.css_paths" />


Use custom resources via ZMI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To add custom CSS or JavaScript resources via ZMI you have to add a property:

* ``zmi_additional_css_paths`` for additional CSS
* ``zmi_additional_js_paths`` for additional JavaScript

The properties can have one of the following types:

* ``string``
* ``ustring``
* ``ulines``

The value of the property has to be one or more paths/URLs to CSS resp.
JavaScript which will be included in the HTML of the ZMI. (Paths have to be
resolvable by the browser aka not simple file system paths.)

Update existing Zope 2 ZMI templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The old Zope 2 styling rules did not allow a modern and responsive design. Now
the Zope 4 ZMI uses some basic CSS class names of the bootstrap CSS framework
and structuring concepts for page layout and forms. A ZMI page usually sequences
following templates nesting the page core:

1. manage_page_header()
2. manage_tabs()
3. page core
4. manage_page_footer()

The page core of any form or object listing ZMI template is starting by the
html element ``<main class="container-fluid">``.
Usually ``<main>`` is nesting a ``p`` element for a help-text and the actual form.
To make specific form styling possible the form-element has following CSS names:

1. zmi-$classname
2. zmi-edit|-add

In general specific functional ZMI elements are declared by a CSS class with a
prefixed ``zmi-`` whereas the basic layout is done by usual bootstrap classes
following the typical element nesting:
any form element has a bootstrap-like form-group structure containing a label
and an input field. Important: The width of the input field is defined by the
nesting ``div`` container using the responsive grid classes
``col-sm-9 col md-10``.
With the classes ``col-sm-3 col-md-2`` for the label, a complete bootstrap row
of 12 is filled.

.. code-block:: html

    <div class="form-group row">
      <label for="title" class="form-label col-sm-3 col-md-2">Title</label>
      <div class="col-sm-9 col-md-10">
        <input id="title" class="form-control" type="text" name="title" value="<dtml-if title>&dtml-title;</dtml-if>" />
      </div>
    </div>

The following buttons are constructed as ``div`` element with the classname
``zmi-controls``; the buttons use systematically the bootstrap class pair
``btn btn-primary``.

.. code-block:: html

    <div class="zmi-controls">
      <input class="btn btn-primary" type="submit" name="submit" value="Save" />
    </div>

The following example code shows a whole restructured DTML template rendering
the Zope 4 ZMI:

**Example: updated DTML template**
(from: ``../Zope/src/OFS/dtml/documentEdit.dtml``)

.. code-block:: html
    :linenos:

    <dtml-var manage_page_header>

    <dtml-var manage_tabs>

    <main class="container-fluid">

      <p class="form-help">
          You may edit the source for this document using the form below. You
          may also upload the source for this document from a local file. Click
          the <em>browse</em> button to select a local file to upload.
      </p>

      <form action="manage_edit" method="post" class="zmi-dtml zmi-edit">

        <dtml-with keyword_args mapping>
          <div class="form-group row">
            <label for="title" class="form-label col-sm-3 col-md-2">Title</label>
            <div class="col-sm-9 col-md-10">
              <input id="title" class="form-control" type="text" name="title"
                     value="<dtml-if title>&dtml-title;</dtml-if>" />
            </div>
          </div>
          <div class="form-group">
            <textarea id="content" data-contenttype="html"
                      class="form-control zmi-code col-sm-12"
                      name="data:text" wrap="off"
                      rows="20"><dtml-var __str__></textarea>
          </div>
        </dtml-with>

        <div class="zmi-controls">
          <dtml-if wl_isLocked>
            <input class="btn btn-primary disabled" type="submit"
                   name="submit" value="Save Changes" disabled="disabled" />
            <span class="badge badge-warning"
                  title="This item has been locked by WebDAV">
              <i class="fa fa-lock"></i>
            </span>
          <dtml-else>
            <input class="btn btn-primary" type="submit" name="submit"
                   value="Save Changes" />
          </dtml-if>
        </div>

      </form>

      <dtml-unless wl_isLocked>
        <form action="manage_upload" method="post"
              enctype="multipart/form-data" class="zmi-upload mt-4">
          <div class="input-group" title="Select Local File for Uploading">
            <div class="custom-file">
              <input type="file" name="file" class="custom-file-input"
                     id="file-data" value=""
                     onchange="$('.custom-file label span').html($(this).val().replace(/^.*(\\|\/|\:)/, ''));" />
              <label class="custom-file-label" for="file-data">
                <span>Choose file</span>
              </label>
            </div>
            <div class="input-group-append">
                <input class="btn btn-outline-secondary" type="submit"
                       value="Upload File" />
            </div>
          </div>
        </form>
      </dtml-unless>

    </main>

    <dtml-var manage_page_footer>

More details
~~~~~~~~~~~~
**Textarea:**
A text area element for editing template code or script code uses the JS
library ``ace`` for syntax high-lighting and line numbering. ``Textarea``
elements which are declared by the CSS class ``zmi-code`` are transformed into
an `ace` editor field. Moreover this element has an attribute
``data-contenttype`` which is needed by ace-editor to determine the fitting
syntax highlighting.  ZPT-Example see:
``../Zope/src/Products/PageTemplates/www/ptEdit.zpt``

**File upload element:**
The file upload element has its own form container (classfied as
``zmi-upload``).  All subsequent elements are nested as ``input-group``
containing a ``div`` classified as ``custom-file`` nesting the actual input
element. An inline JS fired on the ``onchange`` event beautifies the file name
shown after selecting it.  ZPT-Example see:
``../Zope/src/Products/PageTemplates/www/ptEdit.zpt``

**Hints and Warnings:**
Some input fields show additional information; these are added as element
``<small>`` directly following the referred input field. (Both elements are
nested by the width defining ``div`` container). Possible text colors are
declared by typical bootstrap class names like ``text-warning``.

**Icons:**
Zope 4 object classes which are shown in the ZMI have declared a class variable
``zmi_icon``; this string corresponds to an appropriate font icon-CSS class
supplied by the Fontawsome web font (https://fontawesome.com/icons)-

**Tables:**
Bootstrap requires an explicit CSS class ``table`` for any table; especially
long item lists should get an additional CSS class ``table-sm`` and maybe
another class ``table-striped`` for a better readability. Finally it is
recommended to add a specific id attribute like ``zmi-db_info``. The general
table structure is compliant to bootstrap standard table
(https://getbootstrap.com/docs/4.1/content/tables/).

**ZMI-classes:**
All basic styling of the zmi-elements is defined in the CSS file, see:
``../Zope/src/zmi/styles/resources/zmi_base.css``

**Implicit  handling of old Zope 2 ZMI templates:**
Old templates which do not contain the ``<main>`` element are automatically
post-processed by a JavaScript function in the browser. The DOM is minimally
modified, so that old forms will fit *somehow* into the Zope 4 layout. In the
page footer a hint about this automatically customizing is shown.
