##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""Windows Services installer/controller for Zope/ZEO/ZRS instance homes"""

import win32api
import win32con
import win32event
import win32file
import win32pipe
import win32process
import win32security
import win32service
import win32serviceutil
import pywintypes
import time
import os

# the max seconds we're allowed to spend backing off
BACKOFF_MAX = 300
# if the process runs successfully for more than BACKOFF_CLEAR_TIME
# seconds, we reset the backoff stats to their initial values
BACKOFF_CLEAR_TIME = 30
# the initial backoff interval (the amount of time we wait to restart
# a dead process)
BACKOFF_INITIAL_INTERVAL = 5

class Service(win32serviceutil.ServiceFramework):
    """ A class representing a Windows NT service that can manage an
    instance-home-based Zope/ZEO/ZRS processes """

    # The PythonService model requires that an actual on-disk class declaration
    # represent a single service.  Thus, the below definition of start_cmd,
    # must be overridden in a subclass in a file within the instance home for
    # each instance.  The below-defined start_cmd (and _svc_display_name_
    # and _svc_name_) are just examples.

    _svc_name_ = r'Zope-Instance'
    _svc_display_name_ = r'Zope instance at C:\Zope-Instance'

    start_cmd = (
        r'"C:\Program Files\Zope-2.7.0-a1\bin\python.exe" '
        r'"C:\Program Files\Zope-2.7.0-a1\lib\python\Zope\Startup\run.py" '
        r'-C "C:\Zope-Instance\etc\zope.conf"'
        )
    
    capture_io = False
    log_file = None

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        # Create an event which we will use to wait on.
        # The "service stop" request will set this event.
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        # Before we do anything, tell the SCM we are starting the stop process.
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        # stop the process if necessary
        try:
            win32process.TerminateProcess(self.hZope, 0)
        except pywintypes.error:
            # the process may already have been terminated
            pass
        # And set my event.
        win32event.SetEvent(self.hWaitStop)

    def createProcess(self, cmd):
        if self.capture_io:
            return self.createProcessCaptureIO(cmd)
        else:
            return win32process.CreateProcess(
                None, cmd, None, None, 0, 0, None, None,
                win32process.STARTUPINFO()), None

    def logmsg(self, event):
        # log a service event using servicemanager.LogMsg
        from servicemanager import LogMsg, EVENTLOG_INFORMATION_TYPE
        LogMsg(EVENTLOG_INFORMATION_TYPE, event,
               (self._svc_name_, " (%s)" % self._svc_display_name_))

    def info(self, s):
        from servicemanager import LogInfoMsg
        LogInfoMsg("%s (%s): %s" %
                   (self._svc_name_, self._svc_display_name_, s))

    def warning(self, s):
        from servicemanager import LogWarningMsg
        LogWarningMsg("%s (%s): %s" %
                      (self._svc_name_, self._svc_display_name_, s))

    def error(self, s):
        from servicemanager import LogErrorMsg
        LogErrorMsg("%s (%s): %s" %
                    (self._svc_name_, self._svc_display_name_, s))

    def SvcDoRun(self):
        # indicate to Zope that the process is daemon managed (restartable)
        os.environ['ZMANAGED'] = '1'

        # XXX the restart behavior is different here than it is for
        # zdaemon.zdrun.  we should probably do the same thing in both
        # places.

        # daemon behavior:  we want to to restart the process if it
        # dies, but if it dies too many times, we need to give up.

        # we use a simple backoff algorithm to determine whether
        # we should try to restart a dead process:  for each
        # time the process dies unexpectedly, we wait some number of
        # seconds to restart it, as determined by the backoff interval,
        # which doubles each time the process dies.  if we exceed
        # BACKOFF_MAX seconds in cumulative backoff time, we give up.
        # at any time if we successfully run the process for more thab
        # BACKOFF_CLEAR_TIME seconds, the backoff stats are reset.

        # the initial number of seconds between process start attempts
        backoff_interval = BACKOFF_INITIAL_INTERVAL
        # the cumulative backoff seconds counter
        backoff_cumulative = 0

        import servicemanager
        self.logmsg(servicemanager.PYS_SERVICE_STARTED)
        
        while 1:
            start_time = time.time()
            info, handles = self.createProcess(self.start_cmd)
            # XXX integrate handles into the wait and make a loop
            # that reads data and writes it into a logfile
            self.hZope = info[0] # the pid
            if backoff_interval > BACKOFF_INITIAL_INTERVAL:
                self.info("created process")
            rc = win32event.WaitForMultipleObjects(
                (self.hWaitStop, self.hZope) + handles, 0, win32event.INFINITE)
            if rc == win32event.WAIT_OBJECT_0:
                # user sent a stop service request
                self.SvcStop()
                break
            else:
                # user did not send a service stop request, but
                # the process died; this may be an error condition
                status = win32process.GetExitCodeProcess(self.hZope)
                if status == 0:
                    # the user shut the process down from the web
                    # interface (or it otherwise exited cleanly)
                    break
                else:
                    # this was an abormal shutdown.
                    if backoff_cumulative > BACKOFF_MAX:
                        self.error("restarting too frequently; quit")
                        self.SvcStop()
                        break
                    self.warning("sleep %s to avoid rapid restarts"
                                 % backoff_interval)
                    if time.time() - start_time > BACKOFF_CLEAR_TIME:
                        backoff_interval = BACKOFF_INITIAL_INTERVAL
                        backoff_cumulative = 0
                    # XXX Since this is async code, it would be better
                    # done by sending and catching a timed event (a
                    # service stop request will need to wait for us to
                    # stop sleeping), but this works well enough for me.
                    time.sleep(backoff_interval)
                    backoff_cumulative += backoff_interval
                    backoff_interval *= 2

        self.logmsg(servicemanager.PYS_SERVICE_STOPPED)

    def createProcessCaptureIO(self, cmd):
        stdin = self.newPipe()
        stdout = self.newPipe()
        stderr = self.newPipe()

        si = win32process.STARTUPINFO()
        si.hStdInput = stdin[0]
        si.hStdOutput = stdout[1]
        si.hStdError = stderr[1]
        si.dwFlags = (win32process.STARTF_USESTDHANDLES
                      | win32process.STARTF_USESHOWWINDOW)
        si.wShowWindow = win32con.SW_HIDE

        c_stdin = self.dup(stdin[1])
        c_stdout = self.dup(stdout[0])
        c_stderr = self.dup(stderr[0])

        # pass True to allow handles to be inherited.  Inheritance is
        # problematic in general, but should work in the controlled
        # circumstances of a service process.
        info = win32process.CreateProcess(None, cmd, None, None, True, 0,
                                          None, None, si)

        win32file.CloseHandle(stdin[0])
        win32file.CloseHandle(stdout[1])
        win32file.CloseHandle(stderr[1])

        return info, (c_stdin, c_stdout, c_stderr)

    def newPipe(self):
        sa = win32security.SECURITY_ATTRIBUTES()
        sa.bInheritHandle = True
        return win32pipe.CreatePipe(sa, 0)

    def dup(self, pipe):
        # create a duplicate handle that is not inherited, so that
        # it can be closed in the parent.  close the original pipe in
        # the process.
        pid = win32api.GetCurrentProcess()
        dup = win32api.DuplicateHandle(pid, pipe, pid, 0, 0,
                                       win32con.DUPLICATE_SAME_ACCESS)
        win32file.CloseHandle(pipe)
        return dup

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(Service)
