/* Generated automatically from /usr/local/python-1.4/lib/python1.4/config/config.c.in by makesetup. */
/* -*- C -*- ***********************************************
Copyright 1991-1995 by Stichting Mathematisch Centrum, Amsterdam,
The Netherlands.

                        All Rights Reserved

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation, and that the names of Stichting Mathematisch
Centrum or CWI or Corporation for National Research Initiatives or
CNRI not be used in advertising or publicity pertaining to
distribution of the software without specific, written prior
permission.

While CWI is the initial source for this software, a modified version
is made available by the Corporation for National Research Initiatives
(CNRI) at the Internet address ftp://ftp.python.org.

STICHTING MATHEMATISCH CENTRUM AND CNRI DISCLAIM ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL STICHTING MATHEMATISCH
CENTRUM OR CNRI BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL
DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

******************************************************************/

/* Module configuration */

/* !!! !!! !!! This file is edited by the makesetup script !!! !!! !!! */

/* This file contains the table of built-in modules.
   See init_builtin() in import.c. */

#include "Python.h"


extern void initposix();
extern void initsignal();
extern void initsocket();
extern void initthread();
extern void initmath();
extern void initregex();
extern void initstrop();
extern void inittime();
extern void initarray();
extern void initcmath();
extern void initstruct();
extern void initoperator();
extern void initfcntl();
extern void initpwd();
extern void initgrp();
extern void initcrypt();
extern void initselect();
extern void initerrno();
extern void inittermios();
extern void init_xdr();
extern void initaudioop();
extern void initimageop();
extern void initrgbimg();
extern void initmd5();
extern void inittiming();
extern void initrotor();
extern void initsyslog();
extern void initnew();
extern void initbinascii();
extern void initparser();

/* -- ADDMODULE MARKER 1 -- */

extern void PyMarshal_Init();
extern void initimp();

struct _inittab inittab[] = {

	{"posix", initposix},
	{"signal", initsignal},
	{"socket", initsocket},
	{"thread", initthread},
	{"math", initmath},
	{"regex", initregex},
	{"strop", initstrop},
	{"time", inittime},
	{"array", initarray},
	{"cmath", initcmath},
	{"struct", initstruct},
	{"operator", initoperator},
	{"fcntl", initfcntl},
	{"pwd", initpwd},
	{"grp", initgrp},
	{"crypt", initcrypt},
	{"select", initselect},
	{"errno", initerrno},
	{"termios", inittermios},
	{"_xdr", init_xdr},
	{"audioop", initaudioop},
	{"imageop", initimageop},
	{"rgbimg", initrgbimg},
	{"md5", initmd5},
	{"timing", inittiming},
	{"rotor", initrotor},
	{"syslog", initsyslog},
	{"new", initnew},
	{"binascii", initbinascii},
	{"parser", initparser},

/* -- ADDMODULE MARKER 2 -- */

	/* This module "lives in" with marshal.c */
	{"marshal", PyMarshal_Init},

	/* This lives it with import.c */
	{"imp", initimp},

	/* These entries are here for sys.builtin_module_names */
	{"__main__", NULL},
	{"__builtin__", NULL},
	{"sys", NULL},

	/* Sentinel */
	{0, 0}
};
