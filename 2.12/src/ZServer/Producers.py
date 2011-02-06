##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
ZServer pipe utils. These producers basically function as callbacks.
"""

import asyncore
import sys

class ShutdownProducer:
    "shuts down medusa"
    def more(self):
        asyncore.close_all()


class LoggingProducer:
    "logs request"
    def __init__(self, logger, bytes, method='log'):
        self.logger=logger
        self.bytes=bytes
        self.method=method

    def more(self):
        getattr(self.logger, self.method)(self.bytes)
        self.logger=None
        return ''


class CallbackProducer:
    "Performs a callback in the channel's thread"
    def __init__(self, callback):
        self.callback=callback

    def more(self):
        self.callback()
        self.callback=None
        return ''


class file_part_producer:
    "producer wrapper for part of a file[-like] objects"
    # match http_channel's outgoing buffer size
    out_buffer_size = 1<<16

    def __init__(self, file, lock, start, end):
        self.file=file
        self.lock=lock
        self.start=start
        self.end=end

    def more(self):
        end=self.end
        if not end: return ''
        start=self.start
        if start >= end: return ''

        file=self.file
        size=end-start
        bsize=self.out_buffer_size
        if size > bsize: size=bsize

        self.lock.acquire()
        try:
            file.seek(start)
            data = file.read(size)
        finally:
            self.lock.release()

        if data:
            start=start+len(data)
            if start < end:
                self.start=start
                return data

        self.end=0
        del self.file

        return data

class file_close_producer:
    def __init__(self, file):
        self.file=file

    def more(self):
        file=self.file
        if file is not None:
            file.close()
            self.file=None
        return ''

class iterator_producer:
    def __init__(self, iterator):
        self.iterator = iterator

    def more(self):
        try:
            return self.iterator.next()
        except StopIteration:
            return ''
