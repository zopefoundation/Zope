import unittest
import Zope2

import transaction

from zope import component
from zope import interface
from zope.interface.interfaces import IObjectEvent
from zope.testing import cleanup

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from Testing.makerequest import makerequest
from Zope2.App import zcml

Zope2.startup()


class EventLogger(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self._called = []

    def trace(self, ob, event):
        self._called.append((ob.getId(), event.__class__.__name__))

    def called(self):
        return self._called

eventlog = EventLogger()


class ITestItem(interface.Interface):
    pass


@interface.implementer(ITestItem)
class TestItem(SimpleItem):

    def __init__(self, id):
        self.id = id


class ITestFolder(interface.Interface):
    pass


@interface.implementer(ITestFolder)
class TestFolder(Folder):

    def __init__(self, id):
        self.id = id

    def _verifyObjectPaste(self, object, validate_src=1):
        pass  # Always allow


class EventLayer:

    @classmethod
    def setUp(cls):
        cleanup.cleanUp()
        zcml.load_site(force=True)
        component.provideHandler(eventlog.trace, (ITestItem, IObjectEvent))
        component.provideHandler(eventlog.trace, (ITestFolder, IObjectEvent))

    @classmethod
    def tearDown(cls):
        cleanup.cleanUp()


class EventTest(unittest.TestCase):

    layer = EventLayer

    def setUp(self):
        self.app = makerequest(Zope2.app())
        try:
            uf = self.app.acl_users
            uf._doAddUser('manager', 'secret', ['Manager'], [])
            user = uf.getUserById('manager').__of__(uf)
            newSecurityManager(None, user)
        except:
            self.tearDown()
            raise

    def tearDown(self):
        noSecurityManager()
        transaction.abort()
        self.app._p_jar.close()


class TestCopySupport(EventTest):
    '''Tests the order in which events are fired'''

    def setUp(self):
        EventTest.setUp(self)
        # A folder that does not verify pastes
        self.app._setObject('folder', TestFolder('folder'))
        self.folder = getattr(self.app, 'folder')
        # The subfolder we are going to copy/move to
        self.folder._setObject('subfolder', TestFolder('subfolder'))
        self.subfolder = getattr(self.folder, 'subfolder')
        # The document we are going to copy/move
        self.folder._setObject('mydoc', TestItem('mydoc'))
        # Need _p_jars
        transaction.savepoint(1)
        # Reset event log
        eventlog.reset()

    def test_5_COPY(self):
        # Test COPY
        req = self.app.REQUEST
        req.environ['HTTP_DEPTH'] = 'infinity'
        req.environ['HTTP_DESTINATION'] = (
            '%s/subfolder/mydoc' % self.folder.absolute_url())
        self.folder.mydoc.COPY(req, req.RESPONSE)
        self.assertEqual(
            eventlog.called(),
            [('mydoc', 'ObjectCopiedEvent'),
             ('mydoc', 'ObjectWillBeAddedEvent'),
             ('mydoc', 'ObjectAddedEvent'),
             ('subfolder', 'ContainerModifiedEvent'),
             ('mydoc', 'ObjectClonedEvent')]
        )

    def test_6_MOVE(self):
        # Test MOVE
        req = self.app.REQUEST
        req.environ['HTTP_DEPTH'] = 'infinity'
        req.environ['HTTP_DESTINATION'] = (
            '%s/subfolder/mydoc' % self.folder.absolute_url())
        self.folder.mydoc.MOVE(req, req.RESPONSE)
        self.assertEqual(
            eventlog.called(),
            [('mydoc', 'ObjectWillBeMovedEvent'),
             ('mydoc', 'ObjectMovedEvent'),
             ('folder', 'ContainerModifiedEvent'),
             ('subfolder', 'ContainerModifiedEvent')]
        )

    def test_7_DELETE(self):
        # Test DELETE
        req = self.app.REQUEST
        req['URL'] = '%s/mydoc' % self.folder.absolute_url()
        self.folder.mydoc.DELETE(req, req.RESPONSE)
        self.assertEqual(
            eventlog.called(),
            [('mydoc', 'ObjectWillBeRemovedEvent'),
             ('mydoc', 'ObjectRemovedEvent'),
             ('folder', 'ContainerModifiedEvent')]
        )


class TestCopySupportSublocation(EventTest):
    '''Tests the order in which events are fired'''

    def setUp(self):
        EventTest.setUp(self)
        # A folder that does not verify pastes
        self.app._setObject('folder', TestFolder('folder'))
        self.folder = getattr(self.app, 'folder')
        # The subfolder we are going to copy/move to
        self.folder._setObject('subfolder', TestFolder('subfolder'))
        self.subfolder = getattr(self.folder, 'subfolder')
        # The folder we are going to copy/move
        self.folder._setObject('myfolder', TestFolder('myfolder'))
        self.myfolder = getattr(self.folder, 'myfolder')
        # The "sublocation" inside our folder we are going to watch
        self.myfolder._setObject('mydoc', TestItem('mydoc'))
        # Need _p_jars
        transaction.savepoint(1)
        # Reset event log
        eventlog.reset()

    def assertEqual(self, first, second, msg=None):
        # XXX: Compare sets as the order of event handlers cannot be
        #      relied on between objects.
        if not set(first) == set(second):
            raise self.failureException(
                (msg or '%r != %r' % (first, second)))

    def test_5_COPY(self):
        # Test COPY
        req = self.app.REQUEST
        req.environ['HTTP_DEPTH'] = 'infinity'
        req.environ['HTTP_DESTINATION'] = (
            '%s/subfolder/myfolder' % self.folder.absolute_url())
        self.folder.myfolder.COPY(req, req.RESPONSE)
        self.assertEqual(
            eventlog.called(),
            [('myfolder', 'ObjectCopiedEvent'),
             ('mydoc', 'ObjectCopiedEvent'),
             ('myfolder', 'ObjectWillBeAddedEvent'),
             ('mydoc', 'ObjectWillBeAddedEvent'),
             ('myfolder', 'ObjectAddedEvent'),
             ('mydoc', 'ObjectAddedEvent'),
             ('subfolder', 'ContainerModifiedEvent'),
             ('myfolder', 'ObjectClonedEvent'),
             ('mydoc', 'ObjectClonedEvent')]
        )

    def test_6_MOVE(self):
        # Test MOVE
        req = self.app.REQUEST
        req.environ['HTTP_DEPTH'] = 'infinity'
        req.environ['HTTP_DESTINATION'] = (
            '%s/subfolder/myfolder' % self.folder.absolute_url())
        self.folder.myfolder.MOVE(req, req.RESPONSE)
        self.assertEqual(
            eventlog.called(),
            [('myfolder', 'ObjectWillBeMovedEvent'),
             ('mydoc', 'ObjectWillBeMovedEvent'),
             ('myfolder', 'ObjectMovedEvent'),
             ('mydoc', 'ObjectMovedEvent'),
             ('folder', 'ContainerModifiedEvent'),
             ('subfolder', 'ContainerModifiedEvent')]
        )

    def test_7_DELETE(self):
        # Test DELETE
        req = self.app.REQUEST
        req['URL'] = '%s/myfolder' % self.folder.absolute_url()
        self.folder.myfolder.DELETE(req, req.RESPONSE)
        self.assertEqual(
            eventlog.called(),
            [('myfolder', 'ObjectWillBeRemovedEvent'),
             ('mydoc', 'ObjectWillBeRemovedEvent'),
             ('myfolder', 'ObjectRemovedEvent'),
             ('mydoc', 'ObjectRemovedEvent'),
             ('folder', 'ContainerModifiedEvent')]
        )
