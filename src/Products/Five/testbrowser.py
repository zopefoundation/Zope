# BBB

from zope.deferredimport import deprecated

deprecated("Please import from Testing.testbrowser",
    PublisherConnection = 'Testing.testbrowser:PublisherConnection',
    PublisherHTTPHandler = 'Testing.testbrowser:PublisherHTTPHandler',
    PublisherMechanizeBrowser = 'Testing.testbrowser:PublisherMechanizeBrowser',
    Browser = 'Testing.testbrowser:Browser',
)
