''' RemotePS.py

 External Method that allows you to remotely (via XML-RPC, for instance)
 execute restricted Python code.

 For example, create an External Method 'restricted_exec' in your Zope
 root, and you can remotely call:

 foobarsize = s.foo.bar.restricted_exec('len(context.objectIds())')
'''

from Products.PythonScripts.PythonScript import PythonScript
from string import join

def restricted_exec(self, body, varmap=None):
    ps = PythonScript('temp')
    if varmap is None:
        varmap = {}
    ps.ZPythonScript_edit(join(varmap.keys(), ','), body)
    return apply(ps.__of__(self), varmap.values())
