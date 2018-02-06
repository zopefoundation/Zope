.. _ZMI-label:

ZMI
===

ZMI is an abbreviation for `Zope Management Interface`. This is the user
interface rendered when accessing Zope`s management screens using a web
browser.

Bootstrap ZMI
-------------

Since Zope 4.0b4 the ZMI is styled using Twitter bootstrap. The previously used
GIF icons were replaced by font glyphs which are stored in the package
`zmi.icons`_

Inside that package is a table of the `available icons`_ including the names
which are required to use them.

Update packages
+++++++++++++++

If you have a Product or package which contains types, which can be added via
the ZMI, the default icon will be shown.

To use one of the new icons add an attribute named `zmi_icon` to the class. The
value should be one of the names listed on `available icons`_.

.. _`zmi.icons` : https://github.com/zopefoundation/zmi.icons
.. _`available icons` : http://htmlpreview.github.io/?https://github.com/zopefoundation/zmi.icons/blob/master/zmi/icons/resources/demo.html

Use custom icons
++++++++++++++++

To use custom icons (which are not part of `zmi.icons`), you need to subscribe
to ``App.interfaces.IRenderZMIEvent`` to need your resources.

Example from `Products.CMFCore/Products/CMFCore/zmi.py`::

    import App.interfaces
    import cmf.icons
    import zope.component


    @zope.component.adapter(App.interfaces.IRenderZMIEvent)
    def load_assets(event):
        """Load the CMS icons for the ZMI."""
        cmf.icons.cmf_icons.need()

The subscriber is registered in
`Products.CMFCore/Products/CMFCore/event.zcml` like this::

    <subscriber
        handler=".zmi.load_assets" />

You can can `need` arbitrary fanstatic resources in the event subscriber, not
only icon fonts, but also custom CSS and JavaScript.
