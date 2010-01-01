from zope.interface import Interface
from zope.security.zcml import Permission
from zope.configuration.fields import GlobalObject
from zope.configuration.fields import Bool
from zope.schema import ASCII


class IDeprecatedManageAddDeleteDirective(Interface):
    """Call manage_afterAdd & co for these contained content classes.
    """
    class_ = GlobalObject(
        title=u"Class",
        required=True,
        )


class IRegisterClassDirective(Interface):

    """registerClass directive schema.

    Register content with Zope 2.
    """

    class_ = GlobalObject(
        title=u'Instance Class',
        description=u'Dotted name of the class that is registered.',
        required=True
        )

    meta_type = ASCII(
        title=u'Meta Type',
        description=u'A human readable unique identifier for the class.',
        required=True
        )

    permission = Permission(
        title=u'Add Permission',
        description=u'The permission for adding objects of this class.',
        required=True
        )

    addview = ASCII(
        title=u'Add View ID',
        description=u'The ID of the add view used in the ZMI. Consider this '
                    u'required unless you know exactly what you do.',
        default=None,
        required=False
        )

    icon = ASCII(
        title=u'Icon ID',
        description=u'The ID of the icon used in the ZMI.',
        default=None,
        required=False
        )

    global_ = Bool(
        title=u'Global scope?',
        description=u'If "global" is False the class is only available in '
                    u'containers that explicitly allow one of its interfaces.',
        default=True,
        required=False
        )


class IRegisterPackageDirective(Interface):
    """Registers the given Python package which at a minimum fools zope2 into
    thinking of it as a zope2 product.
    """

    package = GlobalObject(
        title=u'Target package',
        required=True
        )

    initialize = GlobalObject(
        title=u'Initialization function to invoke',
        description=u'The dotted name of a function that will get invoked '
                    u'with a ProductContext instance',
        required=False
        )
