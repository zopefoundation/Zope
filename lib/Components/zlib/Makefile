# Generic Makefile for dynamically linked extension modules.
#
# Jim Fulton, Digital Creations, jim@digicool.com


PYTHON=		python1.4
PYTHONHOME=	`$(PYTHON) -c "import sys; print sys.prefix"`
PYTHONVERSION=	`$(PYTHON) -c "import sys; print sys.version[:3]"`

# The following lines should be left as is:
VERSION=	$(PYTHONVERSION)
pyinstalldir=	$(PYTHONHOME)
installdir=	$(PYTHONHOME)
exec_installdir=$(pyinstalldir)
INCLUDEPY=	$(pyinstalldir)/include/python$(VERSION)
LIBP=		$(exec_installdir)/lib/python$(VERSION)
LIBPL=		$(LIBP)/config
PYMAKE=		make -f $(LIBPL)/Makefile
PLATFORM=	`$(PYTHON) -c 'import sys; print sys.platform'`

# LIBSO is the location of platform-dependent dynamically linked 
# extension libraries.  This can be handy when you need to build 
# shared libraries that are not extensions but want to store them
# with other extensions and need to know where they are.
# Leave this line as it is.
LIBSO=		`$(PYMAKE) -s echodestshared`

# Put your module name here:
MODULE=zlibmodule

# Put the object files for your module here:
OBS=$(MODULE).o zlib/libz.a

# Put extra linker options, such as libraries here:
EXTRALD=

# Put Extra compiler options, such as extra -I options, here
CFLAGS=-O -Izlib

# If you have any Python modules, include them here, so that they
# can get installed.
PYMODULES=

bld:
	make bldp PLAT=$(PLATFORM)

bldp: bin bin/$(PLAT) bin/$(PLAT)/$(MODULE).so

bin:
	mkdir bin	

bin/$(PLAT): 
	mkdir bin/$(PLAT)

bin/$(PLAT)/$(MODULE).so: $(MODULE).c
	make clean
	make build
	cp $(MODULE).so bin/$(PLAT)/

build:
	if [ "$(MODULE)" != your-module ]; then \
	  $(PYMAKE) INCLDIR=$(INCLUDEPY) CONFIGINCLDIR=$(LIBPL) \
		ASHAREDMODULE=$(MODULE) \
		'ASHAREDMODULESOBS=$(OBS)' \
		'ASHAREDMODULESEXTRA=$(EXTRALD)' \
		'OPT=$(CFLAGS)' \
		asharedmodule; \
	fi

# Normally we don't install .py files:
install: installso

# But sometimes we may want to:
installpy: install

installso:
	cp bin/$(PLATFORM)/$(MODULE).so \
           $(installdir)/lib/python/Components/$(PLATFORM)

clean::
	-rm -f *.o *.so *~ *# so_locations

