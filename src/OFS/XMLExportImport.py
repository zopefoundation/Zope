##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
from base64 import encodestring
from cStringIO import StringIO
from ZODB.serialize import referencesf
from ZODB.ExportImport import TemporaryFile, export_end_marker
from ZODB.utils import p64
from ZODB.utils import u64
from Shared.DC.xml import ppml


magic='<?xm' # importXML(jar, file, clue)}

def XMLrecord(oid, len, p):
    q=ppml.ToXMLUnpickler
    f=StringIO(p)
    u=q(f)
    id=u64(oid)
    aka=encodestring(oid)[:-1]
    u.idprefix=str(id)+'.'
    p=u.load().__str__(4)
    if f.tell() < len:
        p=p+u.load().__str__(4)
    String='  <record id="%s" aka="%s">\n%s  </record>\n' % (id, aka, p)
    return String

def exportXML(jar, oid, file=None):

    if file is None: file=TemporaryFile()
    elif type(file) is str: file=open(file,'w+b')
    write=file.write
    write('<?xml version="1.0"?>\012<ZopeData>\012')
    ref=referencesf
    oids=[oid]
    done_oids={}
    done=done_oids.has_key
    load=jar._storage.load
    while oids:
        oid=oids[0]
        del oids[0]
        if done(oid): continue
        done_oids[oid]=1
        try:
            try:
                p, serial = load(oid)
            except TypeError:
                # Some places inside the ZODB 3.9 still want a version
                # argument, for example TmpStore from Connection.py
                p, serial = load(oid, None)
        except:
            pass # Ick, a broken reference
        else:
            ref(p, oids)
            write(XMLrecord(oid,len(p),p))
    write('</ZopeData>\n')
    return file

class zopedata:
    def __init__(self, parser, tag, attrs):
        self.file=parser.file
        write=self.file.write
        write('ZEXP')

    def append(self, data):
        file=self.file
        write=file.write
        pos=file.tell()
        file.seek(pos)
        write(data)

def start_zopedata(parser, tag, data):
    return zopedata(parser, tag, data)

def save_zopedata(parser, tag, data):
    file=parser.file
    write=file.write
    pos=file.tell()
    file.seek(pos)
    write(export_end_marker)

def save_record(parser, tag, data):
    file=parser.file
    write=file.write
    pos=file.tell()
    file.seek(pos)
    a=data[1]
    if a.has_key('id'): oid=a['id']
    oid=p64(int(oid))
    v=''
    for x in data[2:]:
        v=v+x
    l=p64(len(v))
    v=oid+l+v
    return v

def importXML(jar, file, clue=''):
    import xml.parsers.expat
    if type(file) is str:
        file=open(file, 'rb')
    outfile=TemporaryFile()
    data=file.read()
    F=ppml.xmlPickler()
    F.end_handlers['record'] = save_record
    F.end_handlers['ZopeData'] = save_zopedata
    F.start_handlers['ZopeData'] = start_zopedata
    F.binary=1
    F.file=outfile
    p=xml.parsers.expat.ParserCreate()
    p.CharacterDataHandler=F.handle_data
    p.StartElementHandler=F.unknown_starttag
    p.EndElementHandler=F.unknown_endtag
    r=p.Parse(data)
    outfile.seek(0)
    return jar.importFile(outfile,clue)
