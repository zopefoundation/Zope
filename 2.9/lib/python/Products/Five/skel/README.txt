This directory contains Zope3-style instance configuration files:

  * ``site.zcml`` is the root node of the instance's ZCML
    configuration tree.

  * ``package-includes`` may contain Zope3-style ZCML slugs to enable
    3rd party packages that are not dropped into ``Products``.

Copy these files to your ``$INSTANCE_HOME/etc`` directory for
customization.  If Five cannot find them there, it falls back to these
skeleton files.
