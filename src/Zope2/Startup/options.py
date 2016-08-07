##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import os
import xml.sax

from ZConfig.loader import SchemaLoader
from ZConfig.schema import SchemaParser
from zdaemon.zdoptions import ZDOptions
from zope.deferredimport import deprecated

# BBB Zope 5.0
_prefix = 'ZServer.Zope2.Startup.options:'
deprecated(
    'Please import from ZServer.Zope2.Startup.options.',
    ZopeOptions=_prefix + 'ZopeOptions',
)


class ConditionalSchemaParser(SchemaParser):
    """
    A SchemaParser with support for conditionally executing import
    directives based on a Python import condition. This is similar to
    ZCML's condition="installed foo" support, shortened to condition="foo".
    """

    def start_import(self, attrs):
        load_import = True
        condition = attrs.get('condition', '').strip()
        if condition:
            try:
                __import__(condition)
            except ImportError:
                load_import = False

        if load_import:
            SchemaParser.start_import(self, attrs)


class ZopeWSGIOptions(ZDOptions):
    """zdaemon based ZopeWSGIOptions to parse a ZConfig schema.
    """

    schemadir = os.path.dirname(os.path.abspath(__file__))
    schemafile = 'wsgischema.xml'

    def load_schema(self):
        if self.schema is None:
            # Load schema
            if self.schemadir is None:
                self.schemadir = os.path.dirname(__file__)
            self.schemafile = os.path.join(self.schemadir, self.schemafile)
            self._conditional_load()

    def _conditional_load(self):
        loader = SchemaLoader()
        # loadURL
        url = loader.normalizeURL(self.schemafile)
        resource = loader.openResource(url)
        try:
            # load / parseResource without caching
            parser = ConditionalSchemaParser(loader, resource.url)
            xml.sax.parse(resource.file, parser)
            self.schema = parser._schema
        finally:
            resource.close()
