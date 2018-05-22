.. _ZMI-label:

ZMI
===

ZMI is an abbreviation for `Zope Management Interface`. This is the user
interface rendered when accessing Zope`s management screens using a web
browser.

Bootstrap ZMI
-------------

Since Zope 4.0b4 the ZMI is styled using Twitter Bootstrap. The previously used
GIF icons were replaced by font glyphs which are stored in the package
`zmi.styles`_ together with the CSS and JavaScript needed by Twitter Bootstrap.

Inside that package is a table of the `available icons`_ including the names
which are required to use them in the ZMI.

Update packages
+++++++++++++++

If you have a Product or package which contains types, which can be added via
the ZMI, the default icon will be shown.

To use one of the new icons add an attribute named `zmi_icon` to the class. The
value should be one of the class of one of the `available icons`_. I.e. to get the 
info (i in a circle) icon you would set attribute `zmi icon` to `'fas fa-info-circle'`

.. _`zmi.styles` : https://github.com/zopefoundation/zmi.styles
.. _`available icons` : https://fontawesome.com/icons?d=gallery&m=free

Use custom icons and resources
++++++++++++++++++++++++++++++

To use custom icons (which are not part of `zmi.styles`) or load custom CSS resp. JavaScript, you have to:

1. create a directory and fill it with your assets
2. register this directory as resource directory
3. register a subscription adapter for :class:`App.interfaces.ICSSPaths` resp.
   :class:`App.interfaces.IJSPaths`. This adapter has to return an iterable of
   paths resp. URLs which should be loaded when rendering the ZMI.

Example taken from `cmf.zmiicons`_:

* Register the resource directory via ZCML:

  .. code-block:: XML

      <browser:resourceDirectory
          name="cmf.zmiicons"
          directory="resources" />

* Create a subscription adapter returning the path to the CSS file:


  .. code-block:: Python

      import zope.component
      import zope.interface


      @zope.component.adapter(zope.interface.Interface)
      def css_paths(context):
          """Return paths to CSS files needed for the Zope 4 ZMI."""
          return (
              '/++resource++cmf.zmiicons/css/cmftello.css',
          )

* Register the subscriber via ZCML:

  .. code-block:: XML

      <subscriber
          provides="App.interfaces.ICSSPaths"
          factory=".css_paths" />


.. _`cmf.zmiicons` : https://github.com/zopefoundation/cmf.zmiicons


Use custom resources via ZMI
++++++++++++++++++++++++++++

To add custom CSS or JavaScript resources via ZMI you have to add a property:

* ``zmi_additional_css_paths`` for additional CSS
* ``zmi_additional_css_paths`` for additional JavaScript

The properties can have one of the following types:

* ``string``
* ``ustring``
* ``lines``
* ``ulines``

The value of the properties have to be paths or URLs to CSS resp. JavaScript
which will be included in the HTML of the ZMI. (Paths have to be resolvable by
the browser aka not simple file system paths.)
