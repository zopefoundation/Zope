##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import sys

from webdav.xmltools import escape

if sys.version_info >= (3, ):
    basestring = str
    unicode = str


def xml_escape(value):
    if not isinstance(value, basestring):
        value = unicode(value)
    if not isinstance(value, unicode):
        value = value.decode('utf-8')
    value = escape(value)
    return value.encode('utf-8')


class DAVPropertySheetMixin(object):

    propstat = ('<d:propstat xmlns:n="%s">\n'
                '  <d:prop>\n'
                '%s\n'
                '  </d:prop>\n'
                '  <d:status>HTTP/1.1 %s</d:status>\n%s'
                '</d:propstat>\n')

    propdesc = ('  <d:responsedescription>\n'
                '  %s\n'
                '  </d:responsedescription>\n')

    def dav__allprop(self, propstat=propstat):
        # DAV helper method - return one or more propstat elements
        # indicating property names and values for all properties.
        result = []
        for item in self._propertyMap():
            name, type = item['id'], item.get('type', 'string')
            value = self.getProperty(name)

            if type == 'tokens':
                value = ' '.join(map(str, value))
            elif type == 'lines':
                value = '\n'.join(map(str, value))
            # check for xml property
            attrs = item.get('meta', {}).get('__xml_attrs__', None)
            if attrs is not None:
                # It's a xml property. Don't escape value.
                attrs = ''.join(' %s="%s"' % n for n in attrs.items())
            else:
                # It's a non-xml property. Escape value.
                attrs = ''
                if not hasattr(self, "dav__" + name):
                    value = xml_escape(value)
            prop = '  <n:%s%s>%s</n:%s>' % (name, attrs, value, name)

            result.append(prop)
        if not result:
            return ''
        result = '\n'.join(result)

        return propstat % (self.xml_namespace(), result, '200 OK', '')

    def dav__propnames(self, propstat=propstat):
        # DAV helper method - return a propstat element indicating
        # property names for all properties in this PropertySheet.
        result = []
        for name in self.propertyIds():
            result.append('  <n:%s/>' % name)
        if not result:
            return ''
        result = '\n'.join(result)
        return propstat % (self.xml_namespace(), result, '200 OK', '')

    def dav__propstat(self, name, result,
                      propstat=propstat, propdesc=propdesc):
        # DAV helper method - return a propstat element indicating
        # property name and value for the requested property.
        xml_id = self.xml_namespace()
        propdict = self._propdict()
        if name not in propdict:
            if xml_id:
                prop = '<n:%s xmlns:n="%s"/>\n' % (name, xml_id)
            else:
                prop = '<%s xmlns=""/>\n' % name
            code = '404 Not Found'
            if code not in result:
                result[code] = [prop]
            else:
                result[code].append(prop)
            return
        else:
            item = propdict[name]
            name, type = item['id'], item.get('type', 'string')
            value = self.getProperty(name)
            if type == 'tokens':
                value = ' '.join(map(str, value))
            elif type == 'lines':
                value = '\n'.join(map(str, value))
            # allow for xml properties
            attrs = item.get('meta', {}).get('__xml_attrs__', None)
            if attrs is not None:
                # It's a xml property. Don't escape value.
                attrs = ''.join(' %s="%s"' % n for n in attrs.items())
            else:
                # It's a non-xml property. Escape value.
                attrs = ''
                if not hasattr(self, 'dav__%s' % name):
                    value = xml_escape(value)
            if xml_id:
                prop = '<n:%s%s xmlns:n="%s">%s</n:%s>\n' % (
                    name, attrs, xml_id, value, name)
            else:
                prop = '<%s%s xmlns="">%s</%s>\n' % (
                    name, attrs, value, name)
            code = '200 OK'
            if code not in result:
                result[code] = [prop]
            else:
                result[code].append(prop)
            return

    del propstat
    del propdesc
