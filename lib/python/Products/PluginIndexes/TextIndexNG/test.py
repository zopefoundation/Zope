#!/usr/bin/env python2.1

from Products.PluginIndexes.TextIndexNG import TextIndexNG
import os, sys, re,traceback, atexit
import readline

histfile = os.path.expanduser('~/.pyhist')
try:
    readline.read_history_file(histfile)
except IOError: pass
atexit.register(readline.write_history_file,histfile)

datadir = '/work/html//doc/python-2.2/lib'
datadir = '/work/html//doc/python-2.2/ext'

class extra: pass


class TO:
    
    def __init__(self,txt):
        self.text = txt


ex = extra()
ex.useSplitter='ZopeSplitter'
ex.useStemmer='porter'
ex.useOperator='and'
ex.lexicon = None
ex.useGlobbing=1


TI = TextIndexNG.TextIndexNG('text',ex)
t1 = TO ('this text is a suxing text')
t2 = TO ('the suxing quick brown fox jumps over the lazy dog because the dog is quick and jumps quick') 
TI.index_object(-1,t1)
TI.index_object(-2,t2)

files = os.listdir(datadir)
files.sort()

for i in range(len(files)):
    f = files[i]
    print f
    fname = os.path.join(datadir,f)
    data = open(fname).read()

    T = TO(data)
    TI.index_object(i,T)



#TI.newTree()
#print 
#print TI._apply_index({'text':{'query':'suxing'}})
#print 
#print TI._apply_index({'text':{'query':'blabla'}})
#print 
#print TI._apply_index({'text':{'query':'suxing and quick'}})
##print TI._apply_index({'text':{'query':'(wurm dog and cat) or dummnase'}})
##print TI._apply_index({'text':{'query':'("wurm dog blabla the" and cat) or dummnase'}})
#print 
#x = TI._apply_index({'text':{'query':'dog and lazy'}})
#print x


while 1:

    line = raw_input("> ")
    
    
    try:
        nums,dummy = TI._apply_index({'text':{'query':line}})

        print "Result:"
        
        for k,v in nums.items():
            print k,files[k]

        print 

    except:
        traceback.print_exc()
    
