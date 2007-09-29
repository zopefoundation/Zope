
import os
import logging
import ZODB

LOG = logging.getLogger('Testing')

def getStorage():

    get = os.environ.get
    # Support for running tests against an existing ZEO storage
    # ATT: better configuration options (ajung, 17.09.2007)

    if os.environ.has_key('TEST_ZEO_HOST') and os.environ.has_key('TEST_ZEO_PORT'):

        from ZEO.ClientStorage import ClientStorage
        zeo_host = get('TEST_ZEO_HOST')
        zeo_port = int(get('TEST_ZEO_PORT'))
        LOG.info('Using ZEO server (%s:%d)' % (zeo_host, zeo_port))
        return ClientStorage((zeo_host, zeo_port))

    elif os.environ.has_key('TEST_FILESTORAGE'):

        import ZODB.FileStorage
        datafs = get('TEST_FILESTORAGE')
        LOG.info('Using Filestorage at (%s)' % datafs)
        return ZODB.FileStorage.FileStorage(datafs)

    else:
        from ZODB.DemoStorage import DemoStorage
        Storage = DemoStorage(quota=(1<<20))
        LOG.info('Using DemoStorage')
        return DemoStorage(quota=(1<<20))

Storage = getStorage()
