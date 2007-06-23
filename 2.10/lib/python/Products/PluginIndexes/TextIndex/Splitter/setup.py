#!/usr/bin/env python

from distutils.core import setup,Extension
import os,exceptions,commands,sys

CFLAGS = []
LFLAGS = []

LIBS=[]


setup (name = "Splitter",
    version = "1.0",
    description = "Splitters for Zope 2.5",
    author = "Andreas Jung",
    author_email = "andreas@zope.com",
    url = "http://www.zope.org/...",
    ext_modules=[
        Extension("ZopeSplitter",['ZopeSplitter/src/ZopeSplitter.c']), \
        Extension("ISO_8859_1_Splitter",['ISO_8859_1_Splitter/src/ISO_8859_1_Splitter.c']),   \
        Extension("UnicodeSplitter",['UnicodeSplitter/src/UnicodeSplitter.c'])   \
        ]
      )
