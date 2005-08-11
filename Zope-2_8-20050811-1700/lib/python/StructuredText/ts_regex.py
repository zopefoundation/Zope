##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Provide a thread-safe interface to regex
"""
import regex, regsub #, Sync
from regex import *
from regsub import split, sub, gsub, splitx, capwords

try:
    import thread
except:
    class allocate_lock:
        def acquire(*args): pass
        def release(*args): pass

else:
    class SafeFunction:
        _l=thread.allocate_lock()
        _a=_l.acquire
        _r=_l.release

        def __init__(self, f):
            self._f=f

        def __call__(self, *args, **kw):
            self._a()
            try: return self._f(*args, **kw)
            finally: self._r()

    split=SafeFunction(split)
    sub=SafeFunction(sub)
    gsub=SafeFunction(gsub)
    splitx=SafeFunction(splitx)
    capwords=SafeFunction(capwords)

    allocate_lock=thread.allocate_lock

class compile:

    _r=None
    groupindex=None

    def __init__(self, *args):
        self._r=r=regex(*compile, **args)
        self._init(r)

    def _init(self, r):
        lock=allocate_lock()
        self.__a=lock.acquire
        self.__r=lock.release
        self.translate=r.translate
        self.givenpat=r.givenpat
        self.realpat=r.realpat

    def match(self, string, pos=0):
        self.__a()
        try: return self._r.match(string, pos)
        finally: self.__r()

    def search(self, string, pos=0):
        self.__a()
        try: return self._r.search(string, pos)
        finally: self.__r()

    def search_group(self, str, group, pos=0):
        """Search a string for a pattern.

        If the pattern was not found, then None is returned,
        otherwise, the location where the pattern was found,
        as well as any specified group are returned.
        """
        self.__a()
        try:
            r=self._r
            l=r.search(str, pos)
            if l < 0: return None
            return l, r.group(*group)
        finally: self.__r()

    def match_group(self, str, group, pos=0):
        """Match a pattern against a string

        If the string does not match the pattern, then None is
        returned, otherwise, the length of the match, as well
        as any specified group are returned.
        """
        self.__a()
        try:
            r=self._r
            l=r.match(str, pos)
            if l < 0: return None
            return l, r.group(*group)
        finally: self.__r()

    def search_regs(self, str, pos=0):
        """Search a string for a pattern.

        If the pattern was not found, then None is returned,
        otherwise, the 'regs' attribute of the expression is
        returned.
        """
        self.__a()
        try:
            r=self._r
            r.search(str, pos)
            return r.regs
        finally: self.__r()

    def match_regs(self, str, pos=0):
        """Match a pattern against a string

        If the string does not match the pattern, then None is
        returned, otherwise, the 'regs' attribute of the expression is
        returned.
        """
        self.__a()
        try:
            r=self._r
            r.match(str, pos)
            return r.regs
        finally: self.__r()

class symcomp(compile):

    def __init__(self, *args):
        self._r=r=regex.symcomp(*args)
        self._init(r)
        self.groupindex=r.groupindex
