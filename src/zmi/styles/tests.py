"""Testing .subscriber.*"""

import Testing.ZopeTestCase
from Products.SiteAccess.VirtualHostMonster import VirtualHostMonster
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
    """Test subscribers URL generation with a user from a user folder
    not at the root.
    """
    request_path = f"/{Testing.ZopeTestCase.folder_name}/manage_main"
    resources_base_path = f"/{Testing.ZopeTestCase.folder_name}"

    def afterSetUp(self):
        if "virtual_hosting" not in self.app:
            vhm = VirtualHostMonster()
            vhm.addToContainer(self.app)

    def call_manage_main(self):
        """Call /folder/manage_main and return the HTML text."""

        def _call_manage_main(self):
            self.setRoles(['Manager'])
            # temporaryPlacelessSetUp insists in creating an interaction
            # which the WSGI publisher does not expect.
            endInteraction()
            response = self.publish(self.request_path, basic=basic_auth)
            return str(response)
        return temporaryPlacelessSetUp(
            _call_manage_main, required_zcml=setupZCML)(self)

    def test_subscriber__css_paths__1(self):
        """The paths it returns are rendered in the ZMI."""
        from .subscriber import css_paths
        body = self.call_manage_main()
        for path in css_paths(None):
            self.assertIn(f'href="{self.resources_base_path}{path}"', body)

    def test_subscriber__js_paths__1(self):
        """The paths it returns are rendered in the ZMI."""
        from .subscriber import js_paths
        body = self.call_manage_main()
        for path in js_paths(None):
            self.assertIn(f'src="{self.resources_base_path}{path}"', body)


class SubscriberTestsUserFromRootUserFolderViewingRootFolder(SubscriberTests):
    """Tests subscribers URL generation with a user from the root acl_users,
    viewing the root of ZMI.
    """

    request_path = "/manage_main"
    resources_base_path = ""

    def _setupFolder(self):
        self.folder = self.app

    def _setupUserFolder(self):
        # we use the user folder from self.app
        pass


class SubscriberTestsUserFromRootUserFolderViewingFolder(SubscriberTests):
    """Tests subscribers URL generation with a user from the root acl_users,
    viewing a folder not at the root of ZMI. In such case, the URLs are not
    relative to that folder, the resources are served from the root.
    """

    request_path = f"/{Testing.ZopeTestCase.folder_name}/manage_main"
    resources_base_path = ""

    def _setupUser(self):
        uf = self.app.acl_users
        uf.userFolderAddUser(
            Testing.ZopeTestCase.user_name,
            Testing.ZopeTestCase.user_password,
            ["Manager"],
            [],
        )

    def setRoles(self, roles, name=...):
        # we set roles in _setupUser
        pass

    def login(self):
        pass


class SubscriberUrlWithVirtualHostingTests(SubscriberTests):
    """Tests subscribers URL generation using virtual host."""

    request_path = (
        "/VirtualHostBase/https/example.org:443/VirtualHostRoot/"
        f"{Testing.ZopeTestCase.folder_name}/manage_main"
    )
    resources_base_path = f"/{Testing.ZopeTestCase.folder_name}"


class SubscriberUrlWithVirtualHostingAndUserFolderInVirtualHostTests(
        SubscriberTests):
    """Tests subscribers URL generation using virtual host, when
    the authentication path is part of the virtual host base.
    """

    request_path = (
        "/VirtualHostBase/https/example.org:443/"
        f"{Testing.ZopeTestCase.folder_name}/VirtualHostRoot/manage_main"
    )
    resources_base_path = ""


class SubscriberUrlWithVirtualHostingAndVHTests(SubscriberTests):
    """Tests subscribers URL generation using virtual host, when
    the authentication path is part of the virtual host base and
    using a "_vh_" path element.
    """

    request_path = (
        "/VirtualHostBase/https/example.org:443"
        f"/{Testing.ZopeTestCase.folder_name}/"
        "VirtualHostRoot/_vh_zz/manage_main"
    )
    resources_base_path = "/zz"
