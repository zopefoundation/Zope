
"""
Objects for packages that have been uninstalled.
"""
import string, SimpleItem, Globals, Acquisition

broken_klasses={}

class BrokenClass(SimpleItem.Item, Acquisition.Explicit):
    _p_changed=0
    meta_type='Broken Because Product is Gone'
    icon='p_/broken'
    product_name='unknown'

    def __getstate__(self):
        raise SystemError, (
            """This object was originally created by a product that
            is no longer installed.  It cannot be updated.
            """)

    manage=manage_main=Globals.HTMLFile('brokenEdit',globals())
    

def Broken(self, oid, klass):
    if broken_klasses.has_key(klass):
        klass=broken_klasses[klass]
    else:
        module, klass = klass
        d={'BrokenClass': BrokenClass}
        exec ("class %s(BrokenClass): ' '; __module__=%s"
              % (klass, `module`)) in d
        broken_klasses[klass]=d[klass]
        klass=d[klass]
        module=string.split(module,'.')
        if len(module) > 2 and module[0]=='Products':
            klass.product_name= module[1]
        klass.title=(
            'This object from the <strong>%s</strong> product '
            'is <strong><font color=red>broken</font></strong>!' %
            klass.product_name)
        klass.info=(
            'This object\'s class was %s in module %s.' %
            (klass.__name__, klass.__module__))
        
    i=klass()
    i._p_oid=oid
    i._p_jar=self
    return i

