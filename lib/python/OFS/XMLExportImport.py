##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import Shared.DC.xml.ppml
ppml=Shared.DC.xml.ppml
from base64 import encodestring
from cStringIO import StringIO
from ZODB.serialize import referencesf
from ZODB.ExportImport import TemporaryFile, export_end_marker

StringType=type('')

magic='<?xm' # importXML(jar, file, clue)}

def XMLrecord(oid, len, p):
    q=ppml.ToXMLUnpickler
    f=StringIO(p)
    u=q(f)
    id=ppml.u64(oid)
    aka=encodestring(oid)[:-1]
    u.idprefix=str(id)+'.'
    p=u.load().__str__(4)
    if f.tell() < len:
        p=p+u.load().__str__(4)
    String='  <record id="%s" aka="%s">\n%s  </record>\n' % (id, aka, p)
    return String

def exportXML(jar, oid, file=None):

    if file is None: file=TemporaryFile()
    elif type(file) is StringType: file=open(file,'w+b')
    write=file.write
    write('<?xml version="1.0"?>\012<ZopeData>\012')
    version=jar._version
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
        try: p, serial = load(oid, version)
        except: pass # Ick, a broken reference
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
    oid=ppml.p64(int(oid))
    v=''
    for x in data[2:]:
        v=v+x
    l=ppml.p64(len(v))
    v=oid+l+v
    return v

def importXML(jar, file, clue=''):
    import Shared.DC.xml.pyexpat.pyexpat
    pyexpat=Shared.DC.xml.pyexpat.pyexpat
    if type(file) is StringType:
        file=open(file)
    outfile=TemporaryFile()
    data=file.read()
    F=ppml.xmlPickler()
    F.end_handlers['record'] = save_record
    F.end_handlers['ZopeData'] = save_zopedata
    F.start_handlers['ZopeData'] = start_zopedata
    F.binary=1
    F.file=outfile
    p=pyexpat.ParserCreate()
    p.CharacterDataHandler=F.handle_data
    p.StartElementHandler=F.unknown_starttag
    p.EndElementHandler=F.unknown_endtag
    r=p.Parse(data)
    outfile.seek(0)
    return jar.importFile(outfile,clue)
