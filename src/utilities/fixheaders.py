
# Script to fix the header files to ZPL 2.1

import os

for dirpath, dirnames, filenames in os.walk('.'):

    for fname in filenames:
        base,ext = os.path.splitext(fname)
        if not ext in ('.py', '.c', '.h'): continue
        fullname = os.path.join(dirpath, fname)
        if '.svn' in fullname: continue
        data = open(fullname).read()

        changed = False
        if 'Version 2.1 (ZPL)' in data:
            data = data.replace('Version 2.1 (ZPL)', 'Version 2.1 (ZPL)')
            changed = True

        if '(c) 2002 Zope Corporation' in data:
            data = data.replace('(c) 2002 Zope Corporation', '(c) 2002 Zope Corporation')
            changed = True

        print fullname, changed
        if changed:
            open(fullname, 'w').write(data)
