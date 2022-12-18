import Testing.ZopeTestCase


class TestMessageDialog(Testing.ZopeTestCase.ZopeTestCase):

    def test_publish_set_content_type(self):
        from App.Dialogs import MessageDialog

        md = MessageDialog(
            title='dialog title',
            message='dialog message',
            action='action'
        )
        self.assertIn('dialog title', md)
        self.assertIn('dialog message', md)
        self.assertIn('action', md)
        req = self.app.REQUEST
        req.RESPONSE.setBody(md)
        self.assertIn('text/html', req.RESPONSE.getHeader('Content-Type'))
