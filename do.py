"""Shared routines used by the various scripts.

"""
import os, sys, string

for a in sys.argv[1:]:
    n,v = string.split(a,'=')
    os.environ[n]=v

def do(command, picky=1):
    print command
    i=os.system(command)
    if i and picky: raise SystemError, i

def make(*args):
    print
    print '-'*48
    print 'Compiling extensions in %s' % string.join(args,'/')
    
    for a in args: os.chdir(a)
    do('make -f Makefile.pre boot PYTHON=%s' % sys.executable)
    do('make')
    do('make clean')
    for a in args: os.chdir('..')
