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

import time, thread

class DebugLogger:
    """
    Logs debugging information about how ZServer is handling requests
    and responses. This log can be used to help locate troublesome requests.
    
    The format is:
    
        <code> <request id> <time> <data>
    
    where:
    
        'code' is B for begin, I for received input, A for received output,
            E for sent output.
        
        'request id' is a unique request id.
        
        'time' is the time in localtime ISO format.
        
        'data' is the HTTP method and the PATH INFO for B, the size of the input
            for I, the HTTP status code and the size of the output for A, or
            nothing for E.
            
    Note: This facility will be probably be adapted to the zLOG framework.
    """
    
    def __init__(self, filename):
        self.filename = filename
        self.file=open(filename, 'a+b')
        l=thread.allocate_lock()
        self._acquire=l.acquire
        self._release=l.release
        self.log('U', '000000000', 'System startup')
        
    def reopen(self):
        self.file.close()
        self.file=open(self.filename, 'a+b')
        self.log('U', '000000000', 'Logfile reopened')

    def log(self, code, request_id, data=''):
        self._acquire()
        try:
            t=time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(time.time()))
            self.file.write(
                '%s %s %s %s\n' % (code, request_id, t, data)
                )
            self.file.flush()
        finally:
            self._release()


def log(*args): pass

