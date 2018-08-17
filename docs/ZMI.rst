.. _ZMI-label:

ZMI
===

ZMI is an abbreviation for `Zope Management Interface`. This is the user
interface rendered when accessing Zope`s management screens using a web
browser.

Bootstrap ZMI
-------------

Since Zope 4.0b6 the ZMI is styled using Bootstrap. The previously used
GIF icons were replaced by font glyphs which are stored in the package
`zmi.styles`_ together with the CSS and JavaScript needed by Bootstrap.

The free Font Awesome glyphs are used as icons, see the table of
`available icons`_.

Update packages
+++++++++++++++

If you have a Product or package which contains types, which can be added via
the ZMI, the default icon will be shown.

To use one of the new icons add an attribute named ``zmi_icon`` to the class.
As value use a name listed on `available icons`_ prefixed by ``fas fa-``.
Example to use the info icon (i in a circle)::

    zmi_icon = 'fas fa-info-circle'

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
++++++++++++++++++++++++++++

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
