from zope.configuration.fields import Bool
from zope.configuration.fields import GlobalObject
from zope.interface import Interface
from zope.schema import ASCII
from zope.security.zcml import Permission


class IDeprecatedManageAddDeleteDirective(Interface):
    """Call manage_afterAdd & co for these contained content classes.
    """
    class_ = GlobalObject(
        title="Class",
        required=True)


class IRegisterClassDirective(Interface):
    """registerClass directive schema.

    Register content with Zope 2.
    """

    class_ = GlobalObject(
        title='Instance Class',
        description='Dotted name of the class that is registered.',
        required=True)

    meta_type = ASCII(
        title='Meta Type',
        description='A human readable unique identifier for the class.',
        required=True)

    permission = Permission(
        title='Add Permission',
        description='The permission for adding objects of this class.',
        required=True)

    addview = ASCII(
        title='Add View ID',
        description='The ID of the add view used in the ZMI. Consider this '
                    'required unless you know exactly what you do.',
        default=None,
        required=False)

    icon = ASCII(
        title='Icon ID',
        description='The ID of the icon used in the ZMI.',
        default=None,
        required=False)

    global_ = Bool(
        title='Global scope?',
        description='If "global" is False the class is only available in '
                    'containers that explicitly allow one of its interfaces.',
        default=True,
        required=False)


class IRegisterPackageDirective(Interface):
    """Registers the given Python package which at a minimum fools zope2 into
    thinking of it as a zope2 product.
    """

    package = GlobalObject(
        title='Target package',
        required=True)

    initialize = GlobalObject(
        title='Initialization function to invoke',
        description='The dotted name of a function that will get invoked '
                    'with a ProductContext instance',
        required=False)
