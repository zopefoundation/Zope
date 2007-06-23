##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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

    # The PythonService model requires that an actual on-disk class declaration
    # represent a single service.  Thus, the definitions below for the instance
    # must be overridden in a subclass in a file within the instance home for
    # each instance.
    # The values below are just examples.
    _svc_name_ = r'Zope-Instance'
    _svc_display_name_ = r'Zope instance at C:\Zope-Instance'

    process_runner = r'C:\Program Files\Zope-2.7.0-a1\bin\python.exe'
    process_args = r'{path_to}\run.py -C {path_to}\zope.conf'
    evtlog_name = 'Zope'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        # Just say "Zope", instead of "Zope_-xxxxx"
        try:
            servicemanager.SetEventSourceName(self.evtlog_name)
        except AttributeError:
            # old pywin32 - that's ok.
            pass
        # Create an event which we will use to wait on.
        # The "service stop" request will set this event.
        # We create it inheritable so we can pass it to the child process, so
        # it too can act on the stop event.
        sa = win32security.SECURITY_ATTRIBUTES()
        sa.bInheritHandle = True

        self.hWaitStop = win32event.CreateEvent(sa, 0, 0, None)
        self.redirect_thread = None

    def SvcStop(self):
        # Before we do anything, tell the SCM we are starting the stop process.
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.onStop()
        # Set the stop event - the main loop takes care of termination.
        win32event.SetEvent(self.hWaitStop)

    # SvcStop only gets triggered when the user explictly stops (or restarts)
    # the service.  To shut the service down cleanly when Windows is shutting
    # down, we also need to hook SvcShutdown.
    SvcShutdown = SvcStop

    def onStop(self):
        # A hook for subclasses to override
        pass

    def createProcess(self, cmd):
        self.start_time = time.time()
        return self.createProcessCaptureIO(cmd)

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
        self.backoff_interval = BACKOFF_INITIAL_INTERVAL
        # the cumulative backoff seconds counter
        self.backoff_cumulative = 0

        self.logmsg(servicemanager.PYS_SERVICE_STARTED)

        while 1:
            # We pass *this* file and the handle as the first 2 params, then
            # the 'normal' startup args.
            # See the bottom of this script for how that is handled.
            cmd = '"%s" %s' % (self.process_runner, self.process_args)
            info = self.createProcess(cmd)
            # info is (hProcess, hThread, pid, tid)
            self.hZope = info[0] # process handle
            # XXX why the test before the log message?
            if self.backoff_interval > BACKOFF_INITIAL_INTERVAL:
                self.info("created process")
            if not (self.run() and self.checkRestart()):
                break

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        # Stop the child process by opening the special named event.
        # We give it 90 seconds to shutdown normally.  If that doesn't
        # stop things, we give it 30 seconds to do a "fast" shutdown.
        # After that, we just knock it on the head.
        winver = sys.getwindowsversion()
        for sig, timeout in ((signal.SIGINT, 30), (signal.SIGTERM, 10)):
            event_name = "Zope-%d-%d" % (info[2], sig)
            # sys.getwindowsversion() -> major, minor, build, platform_id, ver_string
            # for platform_id, 2==VER_PLATFORM_WIN32_NT
            if winver[0] >= 5 and winver[3] == 2:
                event_name = "Global\\" + event_name
            try:
                he = win32event.OpenEvent(win32event.EVENT_MODIFY_STATE, 0,
                                          event_name)
            except win32event.error, details:
                if details[0] == winerror.ERROR_FILE_NOT_FOUND:
                    # process already dead!
                    break
                # no other expected error - report it.
                self.warning("Failed to open child shutdown event %s"
                             % (event_name,))
                continue

            win32event.SetEvent(he)
            # It should be shutting down now - wait for termination, reporting
            # progress as we go.
            for i in range(timeout):
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                rc = win32event.WaitForSingleObject(self.hZope, 3000)
                if rc == win32event.WAIT_OBJECT_0:
                    break
            # Process terminated - no need to try harder.
            if rc == win32event.WAIT_OBJECT_0:
                break

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        # If necessary, kill it
        if win32process.GetExitCodeProcess(self.hZope)==win32con.STILL_ACTIVE:
            win32api.TerminateProcess(self.hZope, 3)
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        # Wait for the redirect thread - it should have died as the remote
        # process terminated.
        # As we are shutting down, we do the join with a little more care,
        # reporting progress as we wait (even though we never will <wink>)
        if self.redirect_thread is not None:
            for i in range(5):
                self.redirect_thread.join(1)
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                if not self.redirect_thread.isAlive():
                    break
            else:
                self.warning("Redirect thread did not stop!")
        self.logmsg(servicemanager.PYS_SERVICE_STOPPED)

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
            # user sent a stop service request
            keep_running = False
        elif rc == win32event.WAIT_OBJECT_0 + 1:
            # user did not send a service stop request, but
            # the process died; this may be an error condition
            status = win32process.GetExitCodeProcess(self.hZope)
            # exit status 0 means the user caused a clean shutdown,
            # presumably via the web interface.  Any other status
            # is an error that gets written to the event log.
            if status != 0:
                # This should never block - the child process terminating
                # has closed the redirection pipe, so our thread dies.
                self.redirect_thread.join(5)
                if self.redirect_thread.isAlive():
                    self.warning("Redirect thread did not stop!")
                self.warning("process terminated with exit code %d.\n%s" \
                             % (status, "".join(self.captured_blocks)))
            keep_running = status != 0
        else:
            # No other valid return codes.
            assert 0, rc
        return keep_running

    def checkRestart(self):
        # this was an abormal shutdown.
        if self.backoff_cumulative > BACKOFF_MAX:
            self.error("restarting too frequently; quit")
            return False
        self.warning("sleep %s to avoid rapid restarts"
                     % self.backoff_interval)
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

    def createProcessCaptureIO(self, cmd):
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
        t = threading.Thread(target=self.redirectCaptureThread,
                             args = (hOutRead,))
        t.start()
        self.redirect_thread = t
        return info

    def redirectCaptureThread(self, handle):
        # Only one of these running at a time, and handling both stdout and
        # stderr on a single handle.  The read data is never referenced until
        # the thread dies - so no need for locks around self.captured_blocks.
        self.captured_blocks = []
        #self.info("Redirect thread starting")
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
        #self.info("Redirect capture thread terminating")

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

# Real __main__ bootstrap code is in the instance's service module.
if __name__ == '__main__':
    print "This is a framework module - you don't run it directly."
    print "See your $SOFTWARE_HOME\bin directory for the service script."
    sys.exit(1)
