""" Fix up registry entries on Zope uninstall """
from _winreg import *
import sys

def manageZopeRegEntries(uninstalling):
    """ Called at uninstall time from innosetup installer to
    manage the 'current' and 'previous' Zope versions.  This is
    just a convenience to make the Pascal coding in innosetup a little
    less baroque """

    prefix = 'Software\\Zope Corporation'

    try:
        zope = openKeyAllAccess(HKEY_LOCAL_MACHINE, '%s\\Zope\\' % prefix)
    except EnvironmentError:
        # this should never happen (the key is created by ISS)
        return

    try:
        current = QueryValueEx(zope, 'CurrentVersion')[0]
    except WindowsError:
        current = uninstalling
    try:
        previous = QueryValueEx(zope, 'PreviousVersion')[0]
    except WindowsError:
        previous = uninstalling

    if current != uninstalling:
        # someone installed on top of us, punt
        CloseKey(zope)
        return

    # make the previous known version into the current version if it still
    # exists
    try:
        old = openKeyAllAccess(zope, previous)
    except (WindowsError, EnvironmentError):
        pass
    else:
        CloseKey(old)
        SetValueEx(zope, 'CurrentVersion', None, REG_SZ, previous)

    recurseDelete(HKEY_LOCAL_MACHINE, '%s\\Zope\\%s' % (prefix, uninstalling))
    recurseDelete(HKEY_LOCAL_MACHINE, '%s\\Zope\\' % prefix)
    recurseDelete(HKEY_LOCAL_MACHINE, prefix)

def openKeyAllAccess(key, subkey):
    return OpenKey(key, subkey, 0, KEY_ALL_ACCESS)

def recurseDelete(key, subkey):
    """ Delete all keys in subkey that are empty, recursively """
    names = filter(None, subkey.split('\\'))
    done = []
    keys = []
    while names:
        name = names.pop(0)
        done.append(name)
        keyname = '\\'.join(done)
        thiskey = openKeyAllAccess(key, keyname)
        keys.append(thiskey)
        try:
            EnumKey(thiskey, 0)
        except:
            # no subkeys, ok to delete
            DeleteKey(key, keyname)

    for openkey in keys:
        CloseKey(openkey)

if __name__ == '__main__':
    manageZopeRegEntries(sys.argv[1])
        
    
