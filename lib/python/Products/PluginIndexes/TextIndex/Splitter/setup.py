#!/usr/bin/env python 

from distutils.core import setup,Extension 
import os,exceptions,string,commands,sys

CFLAGS = []
LFLAGS = []

LIBS=[]


setup (name = "Splitter",
       version = "1.0",
       description = "Splitters for Zope 2.4",
       author = "Andreas Jung",
       author_email = "andreas@digicool.com",
       url = "http://www.zope.org/...",        
       ext_modules=[Extension("Splitter",['src/Splitter.c']), \
                    Extension("ISO_8859_1_Splitter",['src/ISO_8859_1_Splitter.c'])   \
                   ]
 

      )
