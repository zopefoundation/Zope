# BBB

from zope.deferredimport import deprecated

deprecated("Please import from Zope2.App.zcml",
    _context = 'Zope2.App.zcml:_context',
    _initialized = 'Zope2.App.zcml:_initialized',
    cleanUp = 'Zope2.App.zcml:cleanUp',
    load_config = 'Zope2.App.zcml:load_config',
    load_site = 'Zope2.App.zcml:load_site',
    load_string = 'Zope2.App.zcml:load_string',
)
