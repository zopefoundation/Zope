
import regex, regsub
from regex import *
from regsub import split, sub, gsub, splitx, capwords

try: 
    import thread, Sync

    class compile:

	_r=None

	def __init__(self, *args):
	    self._r=r=apply(regex.compile,args)
	    self.search=r.search
	    self.match=r.match
	    
	def search_group(self, str, group, pos=0):
	    """Search a string for a pattern.

	    If the pattern was not found, then None is returned,
	    otherwise, the location where the pattern was found,
	    as well as any specified group are returned.
	    """
	    r=self._r
	    l=r.search(str, pos)
	    if l < 0: return None
	    return l, apply(r.group, group)

	def match_group(self, str, group, pos=0):
	    """Match a pattern against a string

	    If the string does not match the pattern, then None is
	    returned, otherwise, the length of the match, as well
	    as any specified group are returned.
	    """
	    r=self._r
	    l=r.match(str, pos)
	    if l < 0: return None
	    return l, apply(r.group, group)

	def search_regs(self, str, pos=0):
	    """Search a string for a pattern.

	    If the pattern was not found, then None is returned,
	    otherwise, the 'regs' attribute of the expression is
	    returned.
	    """
	    r=self._r
	    r.search(str, pos)
	    return r.regs

	def match_regs(self, str, pos=0):
	    """Match a pattern against a string

	    If the string does not match the pattern, then None is
	    returned, otherwise, the 'regs' attribute of the expression is
	    returned.
	    """
	    r=self._r
	    r.match(str, pos)
	    return r.regs

	def __getattr__(self, name): return getattr(self._r, name)

    class symcomp(compile):

	def __init__(self, *args):
	    self._r=r=apply(regex.symcomp,args)
	    self.search=r.search
	    self.match=r.match

    class SafeFunction:
	def __init__(self, f):
	    self._f=f
	    l=thread.allocate_lock()
	    self._a=l.acquire
	    self._r=l.release

	def __call__(self, *args, **kw):
	    self._a()
	    try: return apply(self._f, args, kw)
	    finally: self._r()

    split=SafeFunction(split)
    sub=SafeFunction(sub)
    gsub=SafeFunction(gsub)
    splitx=SafeFunction(splitx)
    capwords=SafeFunction(capwords)

except: pass


	
