# Copyright (C) 2004 by Dr. Dieter Maurer, Eichendorffstr. 23, D-66386 St. Ingbert, Germany

from new import function

def rebindFunction(f,rebindDir=None,**rebinds):
  '''return *f* with some globals rebound.'''
  d= {}
  if rebindDir : d.update(rebindDir)
  if rebinds: d.update(rebinds)
  if not d: return f
  f= getattr(f,'im_func',f)
  fd= f.func_globals.copy()
  fd.update(d)
  nf= function(f.func_code,fd,f.func_name,f.func_defaults or ())
  nf.__doc__= f.__doc__
  if f.__dict__ is not None: nf.__dict__= f.__dict__.copy()
  return nf
