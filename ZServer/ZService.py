##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""
ZServer as a NT service.

The serice starts up and monitors a ZServer process.

Features:
  
  * When you start the service it starts ZServer
  * When you stop the serivice it stops ZServer
  * It monitors ZServer and restarts it if it exits abnormally
  * If ZServer is shutdown from the web, the service stops.
  * If ZServer cannot be restarted, the service stops.

TODO:

  * Document it.
  * Integrate it into the Windows installer.
  * Figure out a solution for ZServer information, i.e. remembering/
    setting commandline args, knowing where Python is, etc.
  * Add event logging.  
  * Get Zope version from Zope

This script does for NT the same sort of thing zdeamon.py does for UNIX.
Requires Python win32api extensions.

"""
import win32api, win32serviceutil, win32service, win32event, win32process
import win32evtlog, win32evtlogutil
import time

def get_zope_version():
    # retrieve from Zope
    return "Experimental"

class ZServerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ZServerService"
    _svc_display_name_ = "Zope (%s)" % get_zope_version()
    
    restart_min_time=5 # if ZServer restarts before this many
                       # seconds then we have a problem, and
                       # need to stop the service.
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        dll = win32api.GetModuleFileName(win32api.GetModuleHandle("win32evtlog.pyd"))
        win32evtlogutil.AddSourceToRegistry("Zope",dll)
    
    def SvcDoRun(self):
        self.start_zserver()
        while 1:
            rc=win32event.WaitForMultipleObjects(
                    (self.hWaitStop, self.hZServer), 0, win32event.INFINITE)
            if rc - win32event.WAIT_OBJECT_0 == 0:
                break
            else:
                self.restart_zserver()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING, 5000)   

    def SvcStop(self):
        try:
            self.stop_zserver()
            win32evtlogutil.ReportEvent('Zope', 2,
                 eventType=win32evtlog.EVENTLOG_INFORMATION_TYPE,
                 strings=["Stopping Zope."]
             )
        except:
            pass
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def start_zserver(self):
        result=win32process.CreateProcess(None, self.get_start_command(),
                None, None, 0, 0, None, None, win32process.STARTUPINFO())
        self.hZServer=result[0]
        self.last_start_time=time.time()
        win32evtlogutil.ReportEvent('Zope', 1,
            eventType=win32evtlog.EVENTLOG_INFORMATION_TYPE,
            strings=["Starting Zope."]
            )    
        
    def stop_zserver(self):
        win32process.TerminateProcess(self.hZServer,0)
        
    def restart_zserver(self):
        if time.time() - self.last_start_time < self.restart_min_time:
            win32evtlogutil.ReportEvent('Zope', 4,
                eventType=win32evtlog.EVENTLOG_ERROR_TYPE,
                strings=["Zope died and could not be restarted."]
            ) 
            self.SvcStop()
        code=win32process.GetExitCodeProcess(self.hZServer)
        if code == 0:
            # Exited with a normal status code,
            # assume that shutdown is intentional.
            self.SvcStop()
        else:
            win32evtlogutil.ReportEvent('Zope', 3,
                eventType=win32evtlog.EVENTLOG_WARNING_TYPE,
                strings=["Restarting Zope."]
            ) 
            self.start_zserver()

    def get_start_command(self):
        # where should this info be stored, the registry?
        return '"d:\\program files\\zope1.11.0pr0\\bin\\python.exe" "d:\\program files\\zope1.11.0pr0\\zserver\\mystart.py" -w 8888'
        
if __name__=='__main__':
    win32serviceutil.HandleCommandLine(ZServerService)
    