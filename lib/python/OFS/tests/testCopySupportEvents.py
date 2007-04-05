import unittest
import Testing
import Zope2
Zope2.startup()

import transaction

from Testing.makerequest import makerequest

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager

from OFS.SimpleItem import SimpleItem
from OFS.Folder import Folder

from zope import interface
from zope import component
from zope.app.container.interfaces import IObjectAddedEvent
from zope.app.container.interfaces import IObjectMovedEvent
from zope.app.container.interfaces import IObjectRemovedEvent
from zope.app.container.interfaces import IContainerModifiedEvent
from zope.lifecycleevent.interfaces import IObjectCopiedEvent
from OFS.interfaces import IObjectWillBeAddedEvent
from OFS.interfaces import IObjectWillBeMovedEvent
from OFS.interfaces import IObjectWillBeRemovedEvent
from OFS.interfaces import IObjectClonedEvent

from zope.testing import cleanup
from Products.Five import zcml


class EventLogger(object):
    def __init__(self):
        self.reset()
    def reset(self):
        self._called = []
    def trace(self, ob, event):
        self._called.append((ob.getId(), event))
    def called(self):
        return self._called

eventlog = EventLogger()


class ITestItem(interface.Interface):
    pass

class TestItem(SimpleItem):
    interface.implements(ITestItem)
    def __init__(self, id):
        self.id = id


class ITestFolder(interface.Interface):
    pass

class TestFolder(Folder):
    interface.implements(ITestFolder)
    def __init__(self, id):
        self.id = id
    def _verifyObjectPaste(self, object, validate_src=1):
        pass # Always allow


def objectAddedEvent(ob, event):
    eventlog.trace(ob, 'ObjectAddedEvent')

def objectCopiedEvent(ob, event):
    eventlog.trace(ob, 'ObjectCopiedEvent')

def objectMovedEvent(ob, event):
    if IObjectAddedEvent.providedBy(event):
        return
    if IObjectRemovedEvent.providedBy(event):
        return
    eventlog.trace(ob, 'ObjectMovedEvent')

def objectRemovedEvent(ob, event):
    eventlog.trace(ob, 'ObjectRemovedEvent')

def containerModifiedEvent(ob, event):
    eventlog.trace(ob, 'ContainerModifiedEvent')

def objectWillBeAddedEvent(ob, event):
    eventlog.trace(ob, 'ObjectWillBeAddedEvent')

def objectWillBeMovedEvent(ob, event):
    if IObjectWillBeAddedEvent.providedBy(event):
        return
    if IObjectWillBeRemovedEvent.providedBy(event):
        return
    eventlog.trace(ob, 'ObjectWillBeMovedEvent')

def objectWillBeRemovedEvent(ob, event):
    eventlog.trace(ob, 'ObjectWillBeRemovedEvent')

def objectClonedEvent(ob, event):
    eventlog.trace(ob, 'ObjectClonedEvent')


def setUpItemSubscribers(interface):
    component.provideHandler(objectAddedEvent, (interface, IObjectAddedEvent))
    component.provideHandler(objectCopiedEvent, (interface, IObjectCopiedEvent))
    component.provideHandler(objectMovedEvent, (interface, IObjectMovedEvent))
    component.provideHandler(objectRemovedEvent, (interface, IObjectRemovedEvent))
    component.provideHandler(objectWillBeAddedEvent, (interface, IObjectWillBeAddedEvent))
    component.provideHandler(objectWillBeMovedEvent, (interface, IObjectWillBeMovedEvent))
    component.provideHandler(objectWillBeRemovedEvent, (interface, IObjectWillBeRemovedEvent))
    component.provideHandler(objectClonedEvent, (interface, IObjectClonedEvent))

def setUpFolderSubscribers(interface):
    setUpItemSubscribers(interface)
    component.provideHandler(containerModifiedEvent, (interface, IContainerModifiedEvent))


class EventLayer:

    @classmethod
    def setUp(cls):
        cleanup.cleanUp()
        zcml._initialized = 0
        zcml.load_site()
        setUpItemSubscribers(ITestItem)
        setUpFolderSubscribers(ITestFolder)

    @classmethod
    def tearDown(cls):
        cleanup.cleanUp()
        zcml._initialized = 0


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

    def test_1_Clone(self):
        # Test clone
        self.subfolder.manage_clone(self.folder.mydoc, 'mydoc')
        self.assertEqual(eventlog.called(),
            [('mydoc', 'ObjectCopiedEvent'),
             ('mydoc', 'ObjectWillBeAddedEvent'),
             ('mydoc', 'ObjectAddedEvent'),
             ('subfolder', 'ContainerModifiedEvent'),
             ('mydoc', 'ObjectClonedEvent')]
        )

    def test_2_CopyPaste(self):
        # Test copy/paste
        cb = self.folder.manage_copyObjects(['mydoc'])
        self.subfolder.manage_pasteObjects(cb)
        self.assertEqual(eventlog.called(),
            [('mydoc', 'ObjectCopiedEvent'),
             ('mydoc', 'ObjectWillBeAddedEvent'),
             ('mydoc', 'ObjectAddedEvent'),
             ('subfolder', 'ContainerModifiedEvent'),
             ('mydoc', 'ObjectClonedEvent')]
        )

    def test_3_CutPaste(self):
        # Test cut/paste
        cb = self.folder.manage_cutObjects(['mydoc'])
        self.subfolder.manage_pasteObjects(cb)
        self.assertEqual(eventlog.called(),
            [('mydoc', 'ObjectWillBeMovedEvent'),
             ('mydoc', 'ObjectMovedEvent'),
             ('folder', 'ContainerModifiedEvent'),
             ('subfolder', 'ContainerModifiedEvent')]
        )

    def test_4_Rename(self):
        # Test rename
        self.folder.manage_renameObject('mydoc', 'yourdoc')
        self.assertEqual(eventlog.called(),
            [('mydoc', 'ObjectWillBeMovedEvent'),
             ('yourdoc', 'ObjectMovedEvent'),
             ('folder', 'ContainerModifiedEvent')]
        )

    def test_5_COPY(self):
        # Test webdav COPY
        req = self.app.REQUEST
        req.environ['HTTP_DEPTH'] = 'infinity'
        req.environ['HTTP_DESTINATION'] = '%s/subfolder/mydoc' % self.folder.absolute_url()
        self.folder.mydoc.COPY(req, req.RESPONSE)
        self.assertEqual(eventlog.called(),
            [('mydoc', 'ObjectCopiedEvent'),
             ('mydoc', 'ObjectWillBeAddedEvent'),
             ('mydoc', 'ObjectAddedEvent'),
             ('subfolder', 'ContainerModifiedEvent'),
             ('mydoc', 'ObjectClonedEvent')]
        )

    def test_6_MOVE(self):
        # Test webdav MOVE
        req = self.app.REQUEST
        req.environ['HTTP_DEPTH'] = 'infinity'
        req.environ['HTTP_DESTINATION'] = '%s/subfolder/mydoc' % self.folder.absolute_url()
        self.folder.mydoc.MOVE(req, req.RESPONSE)
        self.assertEqual(eventlog.called(),
            [('mydoc', 'ObjectWillBeMovedEvent'),
             ('mydoc', 'ObjectMovedEvent'),
             ('folder', 'ContainerModifiedEvent'),
             ('subfolder', 'ContainerModifiedEvent')]
        )

    def test_7_DELETE(self):
        # Test webdav DELETE
        req = self.app.REQUEST
        req['URL'] = '%s/mydoc' % self.folder.absolute_url()
        self.folder.mydoc.DELETE(req, req.RESPONSE)
        self.assertEqual(eventlog.called(),
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

    def DISABLED_test_1_Clone(self):
        # Test clone
        self.subfolder.manage_clone(self.folder.myfolder, 'myfolder')
        self.assertEqual(eventlog.called(),
            [#('mydoc', 'ObjectCopiedEvent'),
             ('myfolder', 'ObjectCopiedEvent'),
             ('mydoc', 'ObjectWillBeAddedEvent'),
             ('myfolder', 'ObjectWillBeAddedEvent'),
             ('mydoc', 'ObjectAddedEvent'),
             ('myfolder', 'ObjectAddedEvent'),
             ('subfolder', 'ContainerModifiedEvent'),
             ('mydoc', 'ObjectClonedEvent'),
             ('myfolder', 'ObjectClonedEvent')]
        )

    def DISABLED_test_2_CopyPaste(self):
        # Test copy/paste
        cb = self.folder.manage_copyObjects(['myfolder'])
        self.subfolder.manage_pasteObjects(cb)
        self.assertEqual(eventlog.called(),
            [#('mydoc', 'ObjectCopiedEvent'),
             ('myfolder', 'ObjectCopiedEvent'),
             ('mydoc', 'ObjectWillBeAddedEvent'),
             ('myfolder', 'ObjectWillBeAddedEvent'),
             ('mydoc', 'ObjectAddedEvent'),
             ('myfolder', 'ObjectAddedEvent'),
             ('subfolder', 'ContainerModifiedEvent'),
             ('mydoc', 'ObjectClonedEvent'),
             ('myfolder', 'ObjectClonedEvent')]
        )

    def test_3_CutPaste(self):
        # Test cut/paste
        cb = self.folder.manage_cutObjects(['myfolder'])
        self.subfolder.manage_pasteObjects(cb)
        self.assertEqual(eventlog.called(),
            [('mydoc', 'ObjectWillBeMovedEvent'),
             ('myfolder', 'ObjectWillBeMovedEvent'),
             ('mydoc', 'ObjectMovedEvent'),
             ('myfolder', 'ObjectMovedEvent'),
             ('folder', 'ContainerModifiedEvent'),
             ('subfolder', 'ContainerModifiedEvent')]
        )

    def test_4_Rename(self):
        # Test rename
        self.folder.manage_renameObject('myfolder', 'yourfolder')
        self.assertEqual(eventlog.called(),
            [('mydoc', 'ObjectWillBeMovedEvent'),
             ('myfolder', 'ObjectWillBeMovedEvent'),
             ('mydoc', 'ObjectMovedEvent'),
             ('yourfolder', 'ObjectMovedEvent'),
             ('folder', 'ContainerModifiedEvent')]
        )

    def DISABLED_test_5_COPY(self):
        # Test webdav COPY
        req = self.app.REQUEST
        req.environ['HTTP_DEPTH'] = 'infinity'
        req.environ['HTTP_DESTINATION'] = '%s/subfolder/myfolder' % self.folder.absolute_url()
        self.folder.myfolder.COPY(req, req.RESPONSE)
        self.assertEqual(eventlog.called(),
            [#('mydoc', 'ObjectCopiedEvent'),
             ('myfolder', 'ObjectCopiedEvent'),
             ('mydoc', 'ObjectWillBeAddedEvent'),
             ('myfolder', 'ObjectWillBeAddedEvent'),
             ('mydoc', 'ObjectAddedEvent'),
             ('myfolder', 'ObjectAddedEvent'),
             ('subfolder', 'ContainerModifiedEvent'),
             ('mydoc', 'ObjectClonedEvent'),
             ('myfolder', 'ObjectClonedEvent')]
        )

    def test_6_MOVE(self):
        # Test webdav MOVE
        req = self.app.REQUEST
        req.environ['HTTP_DEPTH'] = 'infinity'
        req.environ['HTTP_DESTINATION'] = '%s/subfolder/myfolder' % self.folder.absolute_url()
        self.folder.myfolder.MOVE(req, req.RESPONSE)
        self.assertEqual(eventlog.called(),
            [('mydoc', 'ObjectWillBeMovedEvent'),
             ('myfolder', 'ObjectWillBeMovedEvent'),
             ('mydoc', 'ObjectMovedEvent'),
             ('myfolder', 'ObjectMovedEvent'),
             ('folder', 'ContainerModifiedEvent'),
             ('subfolder', 'ContainerModifiedEvent')]
        )

    def DISABLED_test_7_DELETE(self):
        # Test webdav DELETE
        req = self.app.REQUEST
        req['URL'] = '%s/myfolder' % self.folder.absolute_url()
        self.folder.myfolder.DELETE(req, req.RESPONSE)
        self.assertEqual(eventlog.called(),
            [('mydoc', 'ObjectWillBeRemovedEvent'),
             ('myfolder', 'ObjectWillBeRemovedEvent'),
             ('mydoc', 'ObjectRemovedEvent'),
             ('myfolder', 'ObjectRemovedEvent'),
             ('folder', 'ContainerModifiedEvent')]
        )


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestCopySupport))
    suite.addTest(makeSuite(TestCopySupportSublocation))
    return suite

