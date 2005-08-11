##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Utils to be reused

$Id: ReuseUtils.py 12912 2005-05-31 09:58:59Z philikon $
"""
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
