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
"""
ZServer as a NT service.

The serice starts up and monitors a ZServer process.

Features:

  * When you start the service it starts ZServer
  * When you stop the serivice it stops ZServer
  * It monitors ZServer and restarts it if it exits abnormally
  * If ZServer is shutdown from the web, the service stops.
  * If ZServer cannot be restarted, the service stops.

Usage:

  Installation

    The ZServer service should be installed by the Zope Windows
    installer. You can manually install, uninstall the service from
    the commandline.

      ZService.py [options] install|update|remove|start [...]
          |stop|restart [...]|debug [...]

    Options for 'install' and 'update' commands only:

     --username domain\username : The Username the service is to run
                                  under

     --password password : The password for the username

     --startup [manual|auto|disabled] : How the service starts,
                                        default = manual

    Commands

      install : Installs the service

      update : Updates the service, use this when you change
               ZServer.py

      remove : Removes the service

      start : Starts the service, this can also be done from the
              services control panel

      stop : Stops the service, this can also be done from the
             services control panel

      restart : Restarts the service

      debug : Runs the service in debug mode

    You can view the usage options by running ZServer.py without any
    arguments.

    Note: you may have to register the Python service program first,

      win32\pythonservice.exe /register

  Starting Zope

    Start Zope by clicking the 'start' button in the services control
    panel. You can set Zope to automatically start at boot time by
    choosing 'Auto' startup by clicking the 'statup' button.

  Stopping Zope

    Stop Zope by clicking the 'stop' button in the services control
    panel. You can also stop Zope through the web by going to the
    Zope control panel and by clicking 'Shutdown'.

  Event logging

    Zope events are logged to the NT application event log. Use the
    event viewer to keep track of Zope events.

  Registry Settings

    You can change how the service starts ZServer by editing a registry
    key.

      HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\
        <Service Name>\Parameters\start

    The value of this key is the command which the service uses to
    start ZServer. For example:

      "C:\Program Files\Zope\bin\python.exe"
        "C:\Program Files\Zope\z2.py" -w 8888


TODO:

  * Integrate it into the Windows installer.
  * Add ZLOG logging in addition to event log logging.
  * Make it easier to run multiple Zope services with one Zope install

This script does for NT the same sort of thing zdaemon.py does for UNIX.
Requires Python win32api extensions.
"""
import sys, os,  time, imp

# Some fancy path footwork is required here because we
# may be run from python.exe or lib/win32/PythonService.exe

home=os.path.split(os.path.split(sys.executable)[0])[0]
if sys.executable[-10:]!='python.exe':
    home=os.path.split(home)[0]
    home=os.path.split(home)[0]
sys.path.append(os.path.join(home, 'bin'))
sys.path.append(os.path.join(home, 'ZServer'))
sys.path.append(os.path.join(home, 'bin', 'lib', 'win32'))
sys.path.append(os.path.join(home, 'bin', 'lib', 'win32', 'lib'))


# pythoncom and pywintypes are special, and require these hacks when
# we dont have a standard Python installation around.

import win32api
def magic_import(modulename, filename):
    # by Mark Hammond
    try:
        # See if it does import first!
        return __import__(modulename)
    except ImportError:
        pass
    # win32 can find the DLL name.
    h = win32api.LoadLibrary(filename)
    found = win32api.GetModuleFileName(h)
    # Python can load the module
    mod = imp.load_module(modulename, None, found, ('.dll', 'rb', imp.C_EXTENSION))
    # inject it into the global module list.
    sys.modules[modulename] = mod
    # And finally inject it into the namespace.
    globals()[modulename] = mod
    win32api.FreeLibrary(h)

magic_import('pywintypes','pywintypes21.dll')

import win32serviceutil, win32service, win32event, win32process
try: import servicemanager
except: pass



class ZServerService(win32serviceutil.ServiceFramework):

    # Some trickery to determine the service name. The WISE
    # installer will write an svcname.txt to the ZServer dir
    # that we can use to figure out our service name.

    path=os.path.join(home, 'ZServer', 'svcname.txt')
    file=open(path, 'r')
    _svc_name_=file.readline().strip()
    file.close()

    _svc_display_name_ = "Zope (%s)" % _svc_name_

    restart_min_time=5 # if ZServer restarts before this many
                       # seconds then we have a problem, and
                       # need to stop the service.

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

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
        servicemanager.LogInfoMsg('Stopping Zope.')
        try:
            self.stop_zserver()
        except:
            pass
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def start_zserver(self):
        sc=self.get_start_command()
        result=win32process.CreateProcess(None, self.get_start_command(),
                None, None, 0, 0, None, None, win32process.STARTUPINFO())
        self.hZServer=result[0]
        self.last_start_time=time.time()
        servicemanager.LogInfoMsg('Starting Zope.')

    def stop_zserver(self):
        win32process.TerminateProcess(self.hZServer,0)

    def restart_zserver(self):
        if time.time() - self.last_start_time < self.restart_min_time:
            servicemanager.LogErrorMsg('Zope died and could not be restarted.')
            self.SvcStop()
        code=win32process.GetExitCodeProcess(self.hZServer)
        if code == 0:
            # Exited with a normal status code,
            # assume that shutdown is intentional.
            self.SvcStop()
        else:
            servicemanager.LogWarningMsg('Restarting Zope.')
            self.start_zserver()

    def get_start_command(self):
        return win32serviceutil.GetServiceCustomOption(self,'start')


def set_start_command(value):
    "sets the ZServer start command if the start command is not already set"
    current=win32serviceutil.GetServiceCustomOption(ZServerService,
                                                    'start', None)
    if current is None:
        win32serviceutil.SetServiceCustomOption(ZServerService,'start',value)


if __name__=='__main__':
    win32serviceutil.HandleCommandLine(ZServerService)
    if 'install' in sys.argv:
        command='"%s" "%s" -S' % (sys.executable, os.path.join(home,'z2.py'))
        set_start_command(command)
        print "Setting ZServer start command to:", command
