import Testing.ZopeTestCase
from Testing.ZopeTestCase.placeless import temporaryPlacelessSetUp
from Testing.ZopeTestCase.placeless import zcml
from zope.security.management import endInteraction


basic_auth = "{0.user_name}:{0.user_password}".format(Testing.ZopeTestCase)


def setupZCML():
    """Set up the ZCML needed to render the ZMI and the assets."""
    import AccessControl
    import zmi.styles
    import Zope2.App
    zcml.load_config('meta.zcml', Zope2.App)
    zcml.load_config('permissions.zcml', AccessControl)
    zcml.load_config('traversing.zcml', Zope2.App)
    zcml.load_config('configure.zcml', zmi.styles)


class SubscriberTests(Testing.ZopeTestCase.FunctionalTestCase):
    """Testing .subscriber.*"""

    def call_manage_main(self):
        """Call /folder/manage_main and return the HTML text."""
        def _call_manage_main(self):
            self.setRoles(['Manager'])
            # temporaryPlacelessSetUp insists in creating an interaction
            # which the WSGI publisher does not expect.
            endInteraction()
            response = self.publish(
                f'/{Testing.ZopeTestCase.folder_name}/manage_main',
                basic=basic_auth)
            return str(response)
        return temporaryPlacelessSetUp(
            _call_manage_main, required_zcml=setupZCML)(self)

    def test_subscriber__css_paths__1(self):
        """The paths it returns are rendered in the ZMI."""
        from .subscriber import css_paths
        body = self.call_manage_main()
        for path in css_paths(None):
            self.assertIn(path, body)

    def test_subscriber__js_paths__1(self):
        """The paths it returns are rendered in the ZMI."""
        from .subscriber import js_paths
        body = self.call_manage_main()
        for path in js_paths(None):
            self.assertIn(path, body)
