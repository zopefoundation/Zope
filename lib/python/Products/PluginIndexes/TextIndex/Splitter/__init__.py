import os,sys,exceptions

availableSplitters = (
  ("ZopeSplitter" , "Zope Default Splitter"),
  ("ISO_8859_1_Splitter" , "Werner Strobles ISO-8859-1 Splitter"),
  ("UnicodeSplitter" , "Unicode-aware splitter")
)

splitterNames = map(lambda x: x[0],availableSplitters)

def getSplitter(name=None):

    if not name in splitterNames and name:
        raise exceptions.RuntimeError, "No such splitter '%s'" % name

    if not name: name = splitterNames[0] 
    if not vars().has_key(name):
        exec( "from %s import Splitter as %s" % (name,name))


    return vars()[name]
    


