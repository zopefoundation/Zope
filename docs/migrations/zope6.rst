Migration from Zope 5 to Zope 6
===============================

Zope 6 has switched to declaring namespace packages following the `PEP 420
implicit namespaces <https://peps.python.org/pep-0420/>`_ style. This affects
the following namespaces:

- ``Products``
- ``Shared``
- ``five``
- ``zope``
- ``z3c``
- ``zc``

All Python packages from these namespaces that are direct dependencies of Zope
have been updated to PEP 420 namespaces, but there is no guarantee that
packages not published by the GitHub `zopefoundation` organization are.

.. warning::

    If you use additional packages from the namespaces shown above and you see
    ``ImportError`` messages during Zope startup then you probably have
    some packages that are not PEP 420 compatible. As a temporary workaround
    until there is a compatible version of those packages you can install the
    package ``horse-with-no-namespace`` to make these work again. The final
    fix is to make these remaining packages PEP 420-compatible.


Prerequisites
-------------

* Update your project to run on the latest version of Zope 5.
* Update your project to run on Python 3.10 or higher.
* Make sure there are no error messages in the logs when running Zope or your
  own tests.

Migration
---------

* Switch to use Zope 6 by using its dependencies for your project.
* No additional steps should be necessary if the prerequisites are fulfilled.
  If you see ``ImportError`` messages, see the warning above for a workaround.
