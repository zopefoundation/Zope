##############################################################################
#
# Copyright (c) 2003-2009 Zope Foundation and Contributors.
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

"""Windows Services installer/controller for Zope/ZEO/ZRS instance homes"""

import sys, os, time, threading, signal

import pywintypes
import winerror, win32con
import win32api, win32event, win32file, win32pipe, win32process, win32security
import win32service, win32serviceutil, servicemanager

# the max seconds we're allowed to spend backing off
BACKOFF_MAX = 300
# if the process runs successfully for more than BACKOFF_CLEAR_TIME
# seconds, we reset the backoff stats to their initial values
BACKOFF_CLEAR_TIME = 30
# the initial backoff interval (the amount of time we wait to restart
# a dead process)
BACKOFF_INITIAL_INTERVAL = 5

# We execute a new thread that captures the tail of the output from our child
# process. If the child fails, it is written to the event log.
# This process is unconditional, and the output is never written to disk
# (except obviously via the event log entry)
# Size of the blocks we read from the child process's output.
CHILDCAPTURE_BLOCK_SIZE = 80
# The number of BLOCKSIZE blocks we keep as process output.  This gives
# is 4k, which should be enough to see any tracebacks etc, but not so
# large as to prematurely fill the event log.
CHILDCAPTURE_MAX_BLOCKS = 50

class Service(win32serviceutil.ServiceFramework):
    """Base class for a Windows Server to manage an external process.

    Subclasses can be used to managed an instance home-based Zope or
    ZEO process.  The win32 Python service module registers a specific
    file and class for a service.  To manage an instance, a subclass
    should be created in the instance home.
    """

    evtlog_name = 'Zope'

    def __init__(self, args):

        # We get passed in the service name
        self._svc_name_ = args[0]

        # ...and from that, we can look up the other needed bits
        # from the registry:
        self._svc_display_name_ = self.getReg('DisplayName')
        self._svc_command_ = self.getReg('command',keyname='PythonClass')
        
        win32serviceutil.ServiceFramework.__init__(self, args)

        # Don't use the service name as the event source name:        
        servicemanager.SetEventSourceName(self.evtlog_name)
        
        # Create an event which we will use to wait on.
        # The "service stop" request will set this event.
        # We create it inheritable so we can pass it to the child process, so
        # it too can act on the stop event.
        sa = win32security.SECURITY_ATTRIBUTES()
        sa.bInheritHandle = True
        self.hWaitStop = win32event.CreateEvent(sa, 0, 0, None)

    ### ServiceFramework methods
        
    def SvcDoRun(self):
        # indicate to Zope that the process is daemon managed (restartable)
        os.environ['ZMANAGED'] = '1'

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
        self.backoff_interval = BACKOFF_INITIAL_INTERVAL
        # the cumulative backoff seconds counter
        self.backoff_cumulative = 0

        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.logmsg(servicemanager.PYS_SERVICE_STARTED)
        while 1:
            self.hZope, hThread, pid, tid = self.createProcess(self._svc_command_)
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            keep_running = self.run()
            if not keep_running:
                # The daemon process has asked to stop
                break
            # should we attempt a restart?
            if not self.checkRestart():
                # No, we should not
                break
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stop(pid)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        self.logmsg(servicemanager.PYS_SERVICE_STOPPED)

    def SvcStop(self):
        # Set the stop event - the main loop takes care of termination.
        win32event.SetEvent(self.hWaitStop)

    # SvcStop only gets triggered when the user explictly stops (or restarts)
    # the service.  To shut the service down cleanly when Windows is shutting
    # down, we also need to hook SvcShutdown.
    SvcShutdown = SvcStop

    ### Helper methods
    
    def run(self):
        """Monitor the daemon process.

        Returns True if the service should continue running and
        False if the service process should exit.  On True return,
        the process exited unexpectedly and the caller should restart
        it.
        """
        keep_running = True
        rc = win32event.WaitForMultipleObjects([self.hWaitStop, self.hZope],
                                               0, # bWaitAll
                                               win32event.INFINITE)
        if rc == win32event.WAIT_OBJECT_0:
            # a stop service request was recieved
            keep_running = False
        elif rc == win32event.WAIT_OBJECT_0 + 1:
            # the process died; this may be an error condition
            status = win32process.GetExitCodeProcess(self.hZope)
            # exit status 0 means a clean shutdown,
            # presumably via the web interface.
            keep_running = status != 0
            if keep_running:
                # Any other status is an error so we write it and
                # any output to the event log
                self.warning("Process terminated with exit code %d.\n%s" \
                             % (status, self.getCapturedOutput()))
        else:
            # No other valid return codes.
            assert 0, rc
        return keep_running

    def checkRestart(self):
        # this was an abormal shutdown.
        if self.backoff_cumulative > BACKOFF_MAX:
            self.error("Attempted restarting more than %s times, aborting."
                       % BACKOFF_MAX)
            return False
        self.warning(
            "Process died unexpectedly, will attempt restart after %s seconds."
            % self.backoff_interval
            )
        if time.time() - self.start_time > BACKOFF_CLEAR_TIME:
            self.backoff_interval = BACKOFF_INITIAL_INTERVAL
            self.backoff_cumulative = 0
        # sleep for our backoff, but still respond to stop requests.
        if win32event.WAIT_OBJECT_0 == \
           win32event.WaitForSingleObject(self.hWaitStop,
                                          self.backoff_interval * 1000):
            return False
        self.backoff_cumulative += self.backoff_interval
        self.backoff_interval *= 2
        return True

    def createProcess(self, cmd):
        self.start_time = time.time()
        
        hInputRead, hInputWriteTemp = self.newPipe()
        hOutReadTemp, hOutWrite = self.newPipe()
        pid = win32api.GetCurrentProcess()
        # This one is duplicated as inheritable.
        hErrWrite = win32api.DuplicateHandle(pid, hOutWrite, pid, 0, 1,
                                       win32con.DUPLICATE_SAME_ACCESS)

        # These are non-inheritable duplicates.
        hOutRead = self.dup(hOutReadTemp)
        hInputWrite = self.dup(hInputWriteTemp)
        # dup() closed hOutReadTemp, hInputWriteTemp

        si = win32process.STARTUPINFO()
        si.hStdInput = hInputRead
        si.hStdOutput = hOutWrite
        si.hStdError = hErrWrite
        si.dwFlags = win32process.STARTF_USESTDHANDLES | \
                     win32process.STARTF_USESHOWWINDOW
        si.wShowWindow = win32con.SW_HIDE

        # pass True to allow handles to be inherited.  Inheritance is
        # problematic in general, but should work in the controlled
        # circumstances of a service process.
        create_flags = win32process.CREATE_NEW_CONSOLE
        info = win32process.CreateProcess(None, cmd, None, None, True,
                                          create_flags, None, None, si)
        # (NOTE: these really aren't necessary for Python - they are closed
        # as soon as they are collected)
        hOutWrite.Close()
        hErrWrite.Close()
        hInputRead.Close()
        # We don't use stdin
        hInputWrite.Close()

        # start a thread collecting output
        t = threading.Thread(
            target=self.outputCaptureThread,
            args = (hOutRead,)
            )
        t.start()
        self.output_thread = t
        return info

    def outputCaptureThread(self, handle):
        # Only one of these running at a time, and handling both stdout and
        # stderr on a single handle.  The read data is never referenced until
        # the thread dies - so no need for locks around self.captured_blocks.
        self.captured_blocks = []
        while 1:
            try:
                ec, data = win32file.ReadFile(handle, CHILDCAPTURE_BLOCK_SIZE)
            except pywintypes.error, err:
                # ERROR_BROKEN_PIPE means the child process closed the
                # handle - ie, it terminated.
                if err[0] != winerror.ERROR_BROKEN_PIPE:
                    self.warning("Error reading output from process: %s" % err)
                break
            self.captured_blocks.append(data)
            del self.captured_blocks[CHILDCAPTURE_MAX_BLOCKS:]
        handle.Close()

    def getCapturedOutput(self):
        self.output_thread.join(5)
        if self.output_thread.isAlive():
            self.warning("Output capturing thread failed to terminate!")
        return "".join(self.captured_blocks)

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
        pipe.Close()
        return dup

    def stop(self,pid):
        # call the method that any subclasses out there may implement:
        self.onStop()
        
        winver = sys.getwindowsversion()
        # This is unfortunately needed because runzope.exe is a setuptools
        # generated .exe that spawns off a sub process, so pid would give us
        # the wrong event name.
        child_pid = int(
            open(self.getReg('pid_filename',keyname='PythonClass')).read()
            )
        
        # Stop the child process by sending signals to the special named event.
        for sig, timeout in (
            (signal.SIGINT, 30), # We give it 90 seconds to shutdown normally.
            (signal.SIGTERM, 10) # If that doesn't stop things, we give it 30
                                 # seconds to do a "fast" shutdown.
            ):
            # See the Signals.WinSignalHandler module for
            # the source of this event name
            event_name = "Zope-%d-%d" % (child_pid,sig)
            # sys.getwindowsversion() -> major, minor, build, platform_id, ver_string
            # for platform_id, 2==VER_PLATFORM_WIN32_NT
            if winver[0] >= 5 and winver[3] == 2:
                event_name = "Global\\" + event_name
            try:
                he = win32event.OpenEvent(win32event.EVENT_MODIFY_STATE, 0,
                                          event_name)
            except win32event.error, details:
                # no other expected error - report it.
                self.warning("Failed to open child shutdown event %s"
                             % (event_name,))
                continue

            win32event.SetEvent(he)
            # It should be shutting down now - wait for termination, reporting
            # progress as we go.
            for i in range(timeout):
                # wait for one second
                rc = win32event.WaitForSingleObject(self.hZope, 1000)
                if rc == win32event.WAIT_OBJECT_0:
                    break
            # Process terminated - no need to try harder.
            if rc == win32event.WAIT_OBJECT_0:
                break

        if win32process.GetExitCodeProcess(self.hZope)==win32con.STILL_ACTIVE:
            # None of the signals worked, so kill the process
            self.warning(
                "Terminating process as it could not be gracefully ended"
                )
            win32api.TerminateProcess(self.hZope, 3)

        output = self.getCapturedOutput()
        if output:
            self.info("Process terminated with output:\n"+output)
                
    ### Overridable subclass methods

    def onStop(self):
        # A hook for subclasses to override.
        # Called just before the service is stopped.
        pass

    ### Registry interaction methods
    
    @classmethod
    def openKey(cls,serviceName,keyname=None):
        keypath = "System\\CurrentControlSet\\Services\\"+serviceName
        if keyname:
            keypath += ('\\'+keyname)
        return win32api.RegOpenKey(
            win32con.HKEY_LOCAL_MACHINE,keypath,0,win32con.KEY_ALL_ACCESS
            )
    
    @classmethod
    def setReg(cls,name,value,serviceName=None,keyname='PythonClass'):
        if not serviceName:
            serviceName = cls._svc_name_
        key = cls.openKey(serviceName,keyname)
        try:
            win32api.RegSetValueEx(key, name, 0, win32con.REG_SZ, value)
        finally:
            win32api.RegCloseKey(key)

    def getReg(self,name,keyname=None):
        key = self.openKey(self._svc_name_,keyname)
        return win32api.RegQueryValueEx(key,name)[0]
    
    ### Logging methods
        
    def logmsg(self, event):
        # log a service event using servicemanager.LogMsg
        try:
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                  event,
                                  (self._svc_name_,
                                   " (%s)" % self._svc_display_name_))
        except win32api.error, details:
            # Failed to write a log entry - most likely problem is
            # that the event log is full.  We don't want this to kill us
            try:
                print "FAILED to write INFO event", event, ":", details
            except IOError:
                pass

    def _dolog(self, func, msg):
        try:
            fullmsg = "%s (%s): %s" % \
                      (self._svc_name_, self._svc_display_name_, msg)
            func(fullmsg)
        except win32api.error, details:
            # Failed to write a log entry - most likely problem is
            # that the event log is full.  We don't want this to kill us
            try:
                print "FAILED to write event log entry:", details
                print msg
            except IOError:
                # And if running as a service, its likely our sys.stdout
                # is invalid
                pass

    def info(self, s):
        self._dolog(servicemanager.LogInfoMsg, s)

    def warning(self, s):
        self._dolog(servicemanager.LogWarningMsg, s)

    def error(self, s):
        self._dolog(servicemanager.LogErrorMsg, s)

