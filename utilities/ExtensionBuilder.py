"""Build Python extension modules from Setup files. Particularly
   designed for building extensions for Zope in a way that works
   the same way for *nix and win32. Note that for building Zope
   you need to get the Zope source distribution (binary releases
   do not contain everything needed to build the Zope extensions).

   To use, drop this file into the 'utilities' directory of your
   Zope source installation. Run
   'python ./utilities/ExtensionBuilder.py -h' for usage details.

   Note that this is not supported code. I am making this available
   mainly because the question "how do I build extensions on win32?"
   keeps coming up on the zope mailing list. Hopefully those of you
   wanting to build on win32 will find this useful. As Zope moves to
   support Python 2, I expect distutils to be the standard for Zope
   extensions, so hopefully this is just a short-term hack.

   brian@digicool.com
   """

import sys, os, regex, string, getopt
from exceptions import StandardError


class ExtensionBuilder:
    """An tool for building extension modules. All filesystem path usage
       is relative to the current working directory when the script is
       invoked. Usage: instantiate an ExtensionBuilder and call make(path),
       passing a directory to build, or call makeAll() to build all Python
       extensions found in the current directory and all subdirectories."""

    def getPythonSourcePath(self):
        """Return the path to the root of the Python source installation,
           raises BuildError if no valid source installation can be found."""
        if hasattr(self, 'py_src_path'):
            return self.py_src_path
        py_src_path = sys.exec_prefix
        if (os.path.exists(os.path.join(py_src_path, 'Include')) or
            os.path.exists(os.path.join(py_src_path, 'include'))):
            self.py_src_path = py_src_path
            return py_src_path
        raise BuildError(
            'A Python source installation must be available to build ' \
            'extensions. No valid source installation was found.'
            )

    def getPythonIncludePath(self):
        py_src_path = self.getPythonSourcePath()
        py_inc_path = os.path.join(py_src_path, 'include')
        if os.path.exists(py_inc_path):
            self.py_inc_path = py_inc_path
            return py_inc_path
        py_inc_path = os.path.join(py_src_path, 'Include')
        if os.path.exists(py_inc_path):
            self.py_inc_path = py_inc_path
            return py_inc_path
        raise BuildError(
            'Unable to determine include directory path.'
            )

    def getMakefileTemplatePath(self):
        """Return the path to the prototype extension makefile from the
           Python distribution (Makefile.pre.in). Raises BuildError if
           the prototype makefile cannot be found."""
        if hasattr(self, 'py_makefile_path'):
            return self.py_makefile_path
        py_src_path = self.getPythonSourcePath()
        py_ver_path = 'python%s' % sys.version[:3]
        py_makefile_path = os.path.join(py_src_path, 'lib', py_ver_path,
                                        'config', 'Makefile.pre.in'
                                        )
        if os.path.exists(py_makefile_path):
            self.py_makefile_path = py_makefile_path
            return py_makefile_path
        raise BuildError(
            'The prototype extension makefile (Makefile.pre.in) could not ' \
            'be found.'
            )

    def isValidSetupFile(self, filename):
        """Return true if the file named by filename smells valid."""
        file = open(filename, 'r')
        line = file.readline()
        file.close()
        if line[:9] == '# install':
            return 0
        return 1

    def doCommand(self, command, fail=1, echo=1):
        """Relay command to the system. If fail is true, raise BuildError
           if the system command returns a non-zero value. If echo is true,
           print commands as they are executed."""
        if echo: print command
        result = os.system(command)
        if result and fail:
            raise BuildError(
                'Command "%s" failed with error code: %d' % (command, result)
                )

    def printMessage(self, message):
        """Print a nice little status message."""
        print
        print '-' * 78
        print message
        print '-' * 78
        print

    def makePosix(self, path):
        """Make the extensions in the directory specified by path."""
        path_items = string.split(path, os.sep)
        for name in path_items:
            os.chdir(name)
        self.doCommand('cp %s .' % self.getMakefileTemplatePath())
        self.doCommand('make -f Makefile.pre.in boot PYTHON=%s' % (
            sys.executable
            ))
        self.doCommand('make')
        self.doCommand('make clean')
        for name in path_items:
            os.chdir('..')
        return

    def makeMakefileWin32(self, module, source, srcdir, optlist, args):
        """Create .def and .mak files for an extension."""
        params = {'module': module,
                  'pyhome': self.getPythonSourcePath(),
                  'source': source,
                  'srcdir': srcdir,
                  'cfg': 'Release',
                  }

        includepath = self.getPythonIncludePath()

        params['includes']=string.join(
            ['/I "%s" /I "%s\\PC"' % (includepath, params['pyhome'])] +
            map(lambda i: '/I "%s"' % i, opt(optlist,'I')) +
            map(lambda i: '/D "%s"' % i, opt(optlist,'D')),
            ' ')

        # Note: handling of 'L' or 'l' is currently not working :(
        tmplist = []
        for item in opt(optlist, 'L'):
            item = os.path.join(os.getcwd(), item)
            item = os.path.normpath(item)
            tmplist.append('/libpath:"%s"' % item)
        params['libdirs'] = string.join(tmplist, '')

        tmplist = []
        for item in opt(optlist, 'l'):
            item = os.path.join(os.getcwd(), item)
            item = os.path.normpath(item)
            tmplist.append('/defaultlib:"%s.lib"' % item)
        params['other_libs'] = string.join(tmplist, '')

        params['other_clean_release']=string.join(
            map(lambda o: '\n\t-@erase "%s\\Release\\%s.obj"' % (
                filepath(o), filebase(o)
                ), args),'')

        params['other_clean_debug']=string.join(
            map(lambda o: '\n\t-@erase "%s\\Debug\\%s.obj"' % (
                filepath(o), filebase(o)
                ), args),'')

        params['other_rule']=string.join(
            map(lambda o:
                '"$(INTDIR)\%s.obj" : %s $(DEP_CPP_MOD) "$(INTDIR)"\n'
                '\t$(CPP) $(CPP_PROJ)  %s '
                % (filebase(o), o, o),
                args),'\n')

        params['other_link']=string.join(
            map(lambda o: '\n\t"$(INTDIR)\%s.obj" \\' % filebase(o),
                args),'')

        # Figure out lib file based on py version.
        libname = 'python%s.lib' % string.replace(sys.version[:3], '.', '')
        params['pythonlib'] = libname

        file = open('%s.def' % module, 'w')
        file.write(win32_def % params)
        file.close()

        file = open('%s.mak' % module, 'w')
        file.write(win32_mak % params)
        file.close()


    def makeWin32(self, path):
        """Make the extensions in the directory specified by path.
           Assumes an installation of MS Visual C++ 4.0 or later."""

        ext_line = regex.compile('\([a-z_][a-z0-9_~]*\)[ \t]*'
                                 '\([.a-z_][./a-z0-9_~]*[.]c\)[ \t\n]',
                                 regex.casefold)

        path_items = string.split(path, os.sep)
        for name in path_items:
            os.chdir(name)

        current_dir = os.getcwd()

        if 'Setup.in' in os.listdir(current_dir):
            self.doCommand('copy Setup.in Setup')
        
        # Parse the Setup file. We have to do a lot of work because
        # NMAKE is very stupid about relative paths :( The only way
        # to get things to work relatively reliably is to turn all
        # path references into absolute paths and actually cd to the
        # extension directory before running NMAKE.
        setupfile = open('Setup', 'r')
        for line in setupfile.readlines():
            if line[0] == '#':
                continue
            if ext_line.match(line) >= 0:

                args = string.split(line)
                module = args[0]
                source = args[1]
                if source[:2] == './':
                    continue
                optlist, args = getopt.getopt(args[2:], 'I:D:L:l:')
                for arg in args:
                    if (arg[:1] == '-') or (string.find(arg, '.') < 0):
                        raise BuildError(
                            'Invalid arguments in Setup: %s' % (
                            string.join(args)
                            ))

                tmplist = []
                for key, val in optlist:
                    value = string.replace(val, '/', '\\')
                    if key == '-I':
                        value = os.path.join(current_dir, value)
                        value = os.path.normpath(value)
                    tmplist.append((key, value))
                optlist = tmplist

                tmplist = []
                for arg in args:
                    arg = string.replace(arg, '/', '\\')
                    if '\\' in arg:
                        arg = os.path.join(current_dir, arg)
                        arg = os.path.normpath(arg)
                    tmplist.append(arg)
                args = tmplist

                source = string.replace(source, '/', '\\')
                
                srcdir = filepath(source)
                srcdir = os.path.normpath(os.path.join(os.getcwd(), srcdir))
                
                source = os.path.split(source)[-1]

                os.chdir(srcdir)

                # Build .def and .mak files
                self.makeMakefileWin32(module, source, srcdir, optlist, args)

                # Build extension dlls
                config = 'CFG="%s - Win32 Release"' % module

                self.doCommand('nmake /nologo /f %s.mak %s' % (
                    module, config
                    ))

                self.doCommand('del *.def *.mak')

                os.chdir(current_dir)

                self.doCommand('copy %s\\Release\\%s.dll %s.pyd' % (
                    srcdir, module, module
                    ))

        for name in path_items:
            os.chdir('..')
        return


    if sys.platform == 'win32':
        makeMethod = makeWin32
    else:
        makeMethod = makePosix

    def make(self, path, make_sub=0):
        """Make the extensions in the directory specified by path. If
           the make_sub argument is passed as a true value, build any
           extensions found in all subdirectories."""
        name_list = os.listdir(path)
        if 'Setup' in name_list:
            if self.isValidSetupFile(os.path.join(path, 'Setup')):
                self.printMessage('Building extensions in: %s' % path)
                self.makeMethod(path)
        if not make_sub:
            return
        for name in name_list:
            pathname = os.path.join(path, name)
            if os.path.isdir(pathname):
                self.make(pathname, make_sub)



class BuildError(StandardError):
    """A fatal build exception."""
    pass

def filebase(file):
    return os.path.splitext(os.path.split(file)[1])[0]

def filepath(file):
    parts = os.path.split(file)
    if parts[0] == '':
        return '.'
    return parts[0]

def opt(optlist, name):
    l=filter(lambda t, name='-'+name: t[0]==name, optlist)
    return map(lambda t: t[1], l)




usage="""Usage: %s [options] [path]

This script builds Python extensions on most platforms, including
win32 provided you have MSVC++ 4.0 or higher installed. To compile
on windows, you need to run the vcvars32.bat file included with
MSVC++ to set your shell environment for using command line VC tools
before running this script.

This script is most commonly used to build a Zope source release. To
do that, cd to the root of your Zope installation and run:

python ./utilities/ExtensionBuilder.py -z

Options:

  -p    Specify the location of your Python source tree. If not
        specified, the script will try to figure it out itself
        and complain if it can't.

  -z    Build the Zope source release. Run this from the root of
        a Zope source installation to build all of the standard
        Zope extensions (ignoring others that may be around).

  -a    Build all extensions found in the current working directory
        and all subdirectories.

  -m    Build only a specific extension module (or set of modules)
        found in the directory passed via the -m value. This value
        must be a path *relative* to the current working directory
        when the script is invoked.

"""

def build_all(path):
    builder = ExtensionBuilder()
    builder.make(path, make_sub=1)
    print 'Done!'

def build_dir(path):
    builder = ExtensionBuilder()
    builder.make(path)
    print 'Done!'

def build_zope(path):
    # path is assumed to be Zope root directory
    builder = ExtensionBuilder()

    def system(command, builder=builder):
        command = string.join(string.split(command, '/'), os.sep)
        builder.doCommand(command)

    if path != '.': system('cd %s' % path)

    cp = (sys.platform == 'win32') and 'copy' or 'cp'
    if os.path.exists('./lib/python/Setup20') and sys.version[:1]=='2':
        system('%s ./lib/python/Setup20 ./lib/python/Setup' % cp)
    if os.path.exists('./lib/python/Setup15') and sys.version[:1]=='1':
        system('%s ./lib/python/Setup15 ./lib/python/Setup' % cp)

    # Note that this assumes Zope 2.3.1 b2 or later!
    for item in ('lib/python',
                 'lib/python/DocumentTemplate',
                 'lib/python/ZODB',
                 'lib/python/BTrees',
                 'lib/python/AccessControl',
                 'lib/python/SearchIndex',
                 'lib/python/Shared/DC/xml/pyexpat',
                 'lib/python/Products/PluginIndexes/TextIndex/Splitter/ZopeSplitter',
                 'lib/python/Products/PluginIndexes/TextIndex/Splitter/ISO_8859_1_Splitter',
                 'lib/python/Products/PluginIndexes/TextIndex/Splitter/UnicodeSplitter'
                 ):
        dirpath = string.join(string.split(item, '/'), os.sep)
        builder.make(dirpath)

    if sys.version[:1] != '2':
        os.chdir('lib')
        files=filter(
            lambda f: string.lower(f[:8])=='cpickle.',
            os.listdir('python')
            )
        if files:
            os.chdir('python')
            os.chdir('ZODB')
            for f in files:
                src=os.path.join('..',f)
                try: os.link(src,f)
                except: open(f,'wb').write(open(src,'rb').read())
            os.chdir('..')
            os.chdir('..')
        os.chdir('..')

    print 'Done!'


def main():
    optlist, args=getopt.getopt(sys.argv[1:], 'p:m:azh')
    for key, val in optlist:
        if key == '-p':
            ExtensionBuilder.py_src_path = val
        elif key == '-h':
            print usage
            sys.exit(0)
        elif key == '-a':
            build_all('.')
        elif key == '-m':
            build_dir(val)
        elif key == '-z':
            build_zope('.')
        else:
            print 'Unrecognized option: %s' % key
            print usage
            sys.exit(0)




win32_def="""EXPORTS
	init%(module)s
"""

win32_mak="""# Microsoft Developer Studio Generated NMAKE File, Format Version 4.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Dynamic-Link Library" 0x0102

!IF "$(CFG)" == ""
CFG=%(module)s - Win32 Debug
!MESSAGE No configuration specified.  Defaulting to %(module)s - Win32 Debug.
!ENDIF 

!IF "$(CFG)" != "%(module)s - Win32 Release" && "$(CFG)" !=\\
 "%(module)s - Win32 Debug"
!MESSAGE Invalid configuration "$(CFG)" specified.
!MESSAGE You can specify a configuration when running NMAKE on this makefile
!MESSAGE by defining the macro CFG on the command line.  For example:
!MESSAGE 
!MESSAGE NMAKE /f "%(module)s.mak" CFG="%(module)s - Win32 Debug"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "%(module)s - Win32 Release" (based on\\
 "Win32 (x86) Dynamic-Link Library")
!MESSAGE "%(module)s - Win32 Debug" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE 
!ERROR An invalid configuration is specified.
!ENDIF 

!IF "$(OS)" == "Windows_NT"
NULL=
!ELSE 
NULL=nul
!ENDIF 
################################################################################
# Begin Project
# PROP Target_Last_Scanned "%(module)s - Win32 Debug"
CPP=cl.exe
RSC=rc.exe
MTL=mktyplib.exe

!IF  "$(CFG)" == "%(module)s - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "Release"
# PROP Intermediate_Dir "Release"
# PROP Target_Dir ""
OUTDIR=%(srcdir)s\\Release
INTDIR=%(srcdir)s\\Release

ALL : "$(OUTDIR)\\%(module)s.dll"

CLEAN : 
	-@erase "$(OUTDIR)\\%(module)s.dll"
	-@erase "$(OUTDIR)\\%(module)s.obj"%(other_clean_release)s
	-@erase "$(OUTDIR)\\%(module)s.lib"
	-@erase "$(OUTDIR)\\%(module)s.exp"
	-@erase "$(OUTDIR)\\%(module)s.pch"

"$(OUTDIR)" :
    if not exist "$(OUTDIR)/$(NULL)" mkdir "$(OUTDIR)"

# ADD BASE CPP /nologo /MD /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /YX /c
# ADD CPP /nologo /MD /W3 /GX /O2 %(includes)s /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /YX /c
CPP_PROJ=/nologo /MD /W3 /GX /O2 %(includes)s /D "WIN32" /D\\
 "NDEBUG" /D "_WINDOWS" /Fp"$(INTDIR)\\%(module)s.pch" /YX /Fo"$(INTDIR)/" /c 
CPP_OBJS=$(OUTDIR)/
CPP_SBRS=
# ADD BASE MTL /nologo /D "NDEBUG" /win32
# ADD MTL /nologo /D "NDEBUG" /win32
MTL_PROJ=/nologo /D "NDEBUG" /win32 
# ADD BASE RSC /l 0x409 /d "NDEBUG"
# ADD RSC /l 0x409 /d "NDEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
BSC32_FLAGS=/nologo /o"$(OUTDIR)\\%(module)s.bsc" 
BSC32_SBRS=
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /machine:I386
# ADD LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /machine:I386
LINK32_FLAGS=kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib\\
 advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib\\
 odbccp32.lib /nologo /subsystem:windows /dll /incremental:no\\
 /pdb:"$(OUTDIR)\\%(module)s.pdb" /machine:I386 /def:".\\%(module)s.def"\\
 /out:"$(OUTDIR)\\%(module)s.dll" /implib:"$(OUTDIR)\\%(module)s.lib" %(libdirs)s
DEF_FILE= \\
	".\\%(module)s.def"
LINK32_OBJS= \\
	"$(INTDIR)\\%(module)s.obj" \\%(other_link)s
	"%(pyhome)s\\libs\\%(pythonlib)s"

"$(OUTDIR)\\%(module)s.dll" : "$(OUTDIR)" $(DEF_FILE) $(LINK32_OBJS)
    $(LINK32) @<<
  $(LINK32_FLAGS) $(LINK32_OBJS)
<<

!ELSEIF  "$(CFG)" == "%(module)s - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "Debug"
# PROP BASE Intermediate_Dir "Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "Debug"
# PROP Intermediate_Dir "Debug"
# PROP Target_Dir ""
OUTDIR=%(srcdir)s\\Debug
INTDIR=%(srcdir)s\\Debug

ALL : "$(OUTDIR)\\%(module)s.dll"

CLEAN : 
	-@erase "$(OUTDIR)\\%(module)s.dll"
	-@erase "$(OUTDIR)\\%(module)s.obj"%(other_clean_debug)s
	-@erase "$(OUTDIR)\\%(module)s.ilk"
	-@erase "$(OUTDIR)\\%(module)s.lib"
	-@erase "$(OUTDIR)\\%(module)s.exp"
	-@erase "$(OUTDIR)\\%(module)s.pdb"
	-@erase "$(OUTDIR)\\%(module)s.pch"
	-@erase "$(OUTDIR)\\pcbuild.pdb"
	-@erase "$(OUTDIR)\\pcbuild.idb"

"$(OUTDIR)" :
    if not exist "$(OUTDIR)/$(NULL)" mkdir "$(OUTDIR)"

# ADD BASE CPP /nologo /MDd /W3 /Gm /GX /Zi /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /YX /c
# ADD CPP /nologo /MDd /W3 /Gm /GX /Zi /Od %(includes)s /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /YX /c
CPP_PROJ=/nologo /MDd /W3 /Gm /GX /Zi /Od %(includes)s /D "WIN32"\\
 /D "_DEBUG" /D "_WINDOWS" /Fp"$(INTDIR)/%(module)s.pch" /YX /Fo"$(INTDIR)/"\\
 /Fd"$(INTDIR)/" /c 
CPP_OBJS=$(OUTDIR)/
CPP_SBRS=
# ADD BASE MTL /nologo /D "_DEBUG" /win32
# ADD MTL /nologo /D "_DEBUG" /win32
MTL_PROJ=/nologo /D "_DEBUG" /win32 
# ADD BASE RSC /l 0x409 /d "_DEBUG"
# ADD RSC /l 0x409 /d "_DEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
BSC32_FLAGS=/nologo /o"$(OUTDIR)/%(module)s.bsc" 
BSC32_SBRS=
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /debug /machine:I386
# ADD LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /debug /machine:I386
LINK32_FLAGS=kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib\\
 advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib\\
 odbccp32.lib /nologo /subsystem:windows /dll /incremental:yes\\
 /pdb:"$(OUTDIR)\\%(module)s.pdb" /debug /machine:I386 /def:".\\%(module)s.def"\\
 /out:"$(OUTDIR)\\%(module)s.dll" /implib:"$(OUTDIR)\\%(module)s.lib" %(libdirs)s
DEF_FILE= \\
	".\\%(module)s.def"
LINK32_OBJS= \\
	"$(INTDIR)\\%(module)s.obj" \\%(other_link)s
	"%(pyhome)s\\libs\\%(pythonlib)s"

"$(OUTDIR)\\%(module)s.dll" : "$(OUTDIR)" $(DEF_FILE) $(LINK32_OBJS)
    $(LINK32) @<<
  $(LINK32_FLAGS) $(LINK32_OBJS)
<<

!ENDIF 

.c{$(CPP_OBJS)}.obj:
   $(CPP) $(CPP_PROJ) $<  

.cpp{$(CPP_OBJS)}.obj:
   $(CPP) $(CPP_PROJ) $<  

.cxx{$(CPP_OBJS)}.obj:
   $(CPP) $(CPP_PROJ) $<  

.c{$(CPP_SBRS)}.sbr:
   $(CPP) $(CPP_PROJ) $<  

.cpp{$(CPP_SBRS)}.sbr:
   $(CPP) $(CPP_PROJ) $<  

.cxx{$(CPP_SBRS)}.sbr:
   $(CPP) $(CPP_PROJ) $<  

################################################################################
# Begin Target

# Name "%(module)s - Win32 Release"
# Name "%(module)s - Win32 Debug"

!IF  "$(CFG)" == "%(module)s - Win32 Release"

!ELSEIF  "$(CFG)" == "%(module)s - Win32 Debug"

!ENDIF 

################################################################################
# Begin Source File

SOURCE="%(srcdir)s\\%(source)s"

"$(INTDIR)\\%(module)s.obj" : $(SOURCE) "$(INTDIR)"
%(other_rule)s

# End Source File
################################################################################
# Begin Source File

SOURCE=.\\%(module)s.def

!IF  "$(CFG)" == "%(module)s - Win32 Release"

!ELSEIF  "$(CFG)" == "%(module)s - Win32 Debug"

!ENDIF 

# End Source File
################################################################################
# Begin Source File

SOURCE=%(pyhome)s\\libs\\%(pythonlib)s

!IF  "$(CFG)" == "%(module)s - Win32 Release"

!ELSEIF  "$(CFG)" == "%(module)s - Win32 Debug"

!ENDIF 

# End Source File
################################################################################
# Begin Source File

SOURCE=.\\readme.txt

!IF  "$(CFG)" == "%(module)s - Win32 Release"

!ELSEIF  "$(CFG)" == "%(module)s - Win32 Debug"

!ENDIF 

# End Source File
# End Target
# End Project
################################################################################
"""


if __name__ == '__main__':
    main()
