@echo off

rem Zope source configure script for Win2K.
rem To make and compile Zope you will need MS VC++ 6.0

rem Assumes youre running on 2000/XP (known to not work under Win98/ME,
rem thanks Tim!).  It *might* work under WinNT, but it hasn't been tested.

rem To specify a Python interpreter to use instead of accepting the
rem result of this 'configure' script's autocheck, issue the command
rem "set PYTHON=\path\to\your\python" before running the configure script.

rem If this script doesnt work for you for some reason, instead just run
rem "YOUR_PYTHON_EXECUTABLE inst\configure.py --prefix=ZOPE_TARGET_DIR"
rem to build Zope.

rem $Id: configure.bat,v 1.3 2003/06/21 13:46:56 chrism Exp $
rem $Revision: 1.3 $

set PYTHON_TARGET_VER=2.3
set DEFAULT_PREFIX=C:\Zope
echo.

:getpythonfromenv
 if "%PYTHON%"=="" goto findpython
 if not exist "%PYTHON%" goto nosuchexecutable
 set FOUND_PYTHON=%PYTHON%

:configure
 "%FOUND_PYTHON%" inst\configure.py %1 %2 %3 %4 %5 %6
 if not errorlevel 1 goto :EOF

:usage
 echo configure [--help] [--quiet] [--prefix=target_dir]
 echo           [--build-base=path] [--ignore-largefile] [--ignore-zlib] 
 echo.
 echo Creates a Makefile suitable for building and installing Zope with Visual C++
 echo.
 echo   Options:
 echo     --help              shows usage and quits
 echo     --quiet             suppress nonessential output
 echo     --prefix            the directory in which you wish to install Zope
 echo                         (e.g. --prefix=c:\Program Files\Zope)
 echo                         defaults to c:\Zope
 echo     --build-base        specify a temporary path for build files
 echo     --ignore-largefile  ignore large file support warnings
 echo     --ignore-zlib       ignore warnings about zlib
 echo.
 echo   Special:
 echo     To specify a Python interpreter to use, issue the command
 echo     "set PYTHON=\path\to\your\python\executable" before running
 echo     this script.
 echo.
 goto :EOF

:findpython
 echo Finding a Python interpreter
 regedit /E "%Temp%\python-for-zope.reg" "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Python.exe"
 if not exist "%Temp%\python-for-zope.reg" goto nopython
 for /F "tokens=1* delims==" %%A IN ('TYPE %Temp%\python-for-zope.reg ^| FIND "Python.exe"') DO set FOUND_PYTHON=%%B
 set FOUND_PYTHON=%FOUND_PYTHON:"=%
 echo A Python interpreter was found at %FOUND_PYTHON%
 echo %FOUND_PYTHON% | FIND "%PYTHON_TARGET_VER%" >NUL
 rem if errorlevel 1 goto badpython
 rem del %Temp%\python-for-zope.reg
 goto configure

:badpython
 echo.
 echo !! ERROR !!
 echo The version of Python that has been found on your computer at
 echo %FOUND_PYTHON% is not capable of running Zope.  Use Python
 echo version %PYTHON_TARGET_VER% instead.  Use the PYTHON environment
 echo to specify the path to the Python interpreter you wish to use.
 echo.
 goto usage

:nosuchexecutable
 echo.
 echo !! ERROR !!
 echo The Python interpreter you've specified ("%PYTHON%") via the PYTHON
 echo environment variable does not appear to exist.
 echo.
 goto usage

:nopython
 echo.
 echo !! ERROR !!
 echo Python is not installed on your computer, please install it first
 echo by downloading it from http://www.python.org.  Alternately,
 echo specify the Python interpreter you wish to use via the PYTHON
 echo environment variable.
 echo.
 goto usage

:EOF
 
