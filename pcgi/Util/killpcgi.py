#!/usr/bin/env python
# killpcgi.py - kill a running pcgi process
# Copyright(c) 1998, Jeff Bauer, All rights reserved.

# killpcgi is a convenience script to kill a running
# pcgi process, provided that it is running on a 
# Unix system.  You pass it the path of the pcgi info
# file, and killpcgi will kill the running process and 
# remove the socket/pid files.
#
# killpcgi has been built at the request of several users,
# but you may want to first examine the script and modify it 
# to suit your environment.
#
# Bugs:  skimpy error handling

# 0.3a  minor win32 exception caught
# 0.2a  Added support for NT - 8/8/98
# 0.1a  Initial version

__version__ = "0.3a"

def win32_kill(pid):
    """posix-style kill command for the Win32 environment"""
    import win32api, pywintypes
    try:
        handle = win32api.OpenProcess(1, 0, pid)
    except pywintypes.error:
        return -1
    return (0 != win32api.TerminateProcess(handle, 0))

def killpcgi(pcgiInfoFile):
    import os, sys, string
    delimiter = '='
    pidFile = None
    socketFile = None
    infoFile = open(pcgiInfoFile, 'r')
    for i in infoFile.readlines():
        if delimiter in i:
            n,v = string.split(string.strip(i), delimiter)
            if n == 'PCGI_PID_FILE':
                pidFile = v
            elif n == 'PCGI_SOCKET_FILE':
                socketFile = v
    infoFile.close()

    if pidFile is None:
        print "unknown pid file"
    else:
        f = open(pidFile)
        pid = int(f.read())
        f.close()
        if os.name == 'nt':
            if not win32_kill(pid):
                print "process %d killed" % pid
        elif os.name == 'posix':
            if os.kill(pid, 0):
                print "process %d doesn't appear to be running" % pid
            else:
                # safety measure (exclude it if you're fearless)
                if os.system('/bin/ps -p %d | grep python > /dev/null' % pid):
                    print "process %d doesn't appear to be python" % pid
                else:
                    os.kill(pid, 15)
                    print "process %d killed" % pid
                    # conservative approach: don't remove pid/socket files
                    # unless we're reasonably certain we have killed the 
                    # running process
                    os.unlink(pidFile)
                    if socketFile is not None: 
                        os.unlink(socketFile)
        else:
            print "kill not supported for platform:", os.name

if __name__ == '__main__':
    import sys
    usage = "usage: killpcgi pcgi-info-file"
    if len(sys.argv) < 2:
        print usage
    else:
        killpcgi(sys.argv[1])
