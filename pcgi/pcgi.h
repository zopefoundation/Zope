/* pcgi.h - Persistent CGI header file for pcgi-wrapper.c, parseinfo.c

Copyright (c) 1998, Digital Creations, Fredericksburg, VA, USA.  All
rights reserved. This software includes contributions from Jeff Bauer.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

  o Redistributions of source code must retain the above copyright
    notice, this list of conditions, and the disclaimer that follows.

  o Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions, and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.

  o All advertising materials mentioning features or use of this
    software must display the following acknowledgement:

      This product includes software developed by Digital Creations
      and its contributors.

  o Neither the name of Digital Creations nor the names of its
    contributors may be used to endorse or promote products derived
    from this software without specific prior written permission.


THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS *AS IS* AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

*/

#ifndef PCGI_H
#include <stdlib.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <time.h>
#include <sys/types.h>
#include <sys/stat.h>

#ifdef UNIX
#include <unistd.h>
#include <signal.h>
#include <sys/wait.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/ipc.h>
#include <sys/sem.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#endif
#ifdef WIN32
#include <windows.h>
#include <io.h>
#include <iostream.h>
#include <winsock.h>
#endif

#define MAXLINEBUFFER   12
#define PATHSEP_UNIX    '/'
#define PATHSEP_WIN32   '\\'
#define DEFAULT_SOCK_PORT   7244
/*#define DEFAULT_SOCK_HOST "127.0.0.1"*/
#define MAXPATH 1024
#define PUBLISHER_NAME_1 "pcgi_publisher.py"
#define PUBLISHER_NAME_2 "pcgi_publisher.pyc"
#define PUBLISHER_NAME_3 "pcgi_publisher.pyo"
#define PUBLISHER_NAME_4 "pcgi_publisher"

#define HDRLEN 10
#define HDRFMT "%010ld"

#ifdef  UNIX
#define PATHSEP PATHSEP_UNIX
typedef int                     pcgi_socket;
#endif
#ifdef  WIN32
#define PATHSEP PATHSEP_WIN32
typedef SOCKET                  pcgi_socket;
#define sleep(x)                Sleep(x * 1000)
#define read(x,y,z)             _read(x,y,z)
#define write(x,y,z)            _write(x,y,z)
#define MUTEX_NAME              "pcgiMutex"
#define AUTODELAY       5
#define CONNRETRY       0
#define CONNDELAY       1
#endif
#ifndef CREOSOTE
/* no-op in case someone forgets to remove a spew() in their debug code */
#define spew(x) 
#endif

#ifndef STDIN_FILENO
#define STDIN_FILENO    0
#endif
#ifndef STDOUT_FILENO
#define STDOUT_FILENO   1
#endif
#ifndef STDERR_FILENO
#define STDERR_FILENO   2
#endif

#define MAXSZ           256
#define RKEY            99

#define E_500           "500 Server Error"
#define E_503           "503 Service Unavailable"

#define ERR101_FAILURE_DURING_START "(101) failure during start"
#define ERR102_FAILURE_DURING_CONNECT "(102) failure during connect"
#define ERR103_UNABLE_VERIFY_RUNNING "(103) unable to verify if process is running"
#define ERR104_ENVIRONMENT_SEND "(104) environment send"
#define ERR105_STDIN_SEND "(105) stdin send"
#define ERR106_STDOUT_READ_HEADER "(106) stdout read header"
#define ERR107_BAD_STDOUT_STRLEN "(107) bad stdout strlen"
#define ERR108_STDOUT_READ_BODY "(108) stdout read body"
#define ERR109_STDERR_READ_HEADER "(109 stderr read header"
#define ERR110_BAD_STDERR_STRLEN "(110) bad stderr strlen"
#define ERR111_STDERR_READ_BODY "(111) stderr read body"
#define ERR112_STDOUT_TO_SERVER "(112) error returning stdout to server"
#define ERR113_STDOUT_TO_SERVER "(113) error returning stderr to server"
#define ERR114_UNABLE_TO_OPEN_SOCKET "(114) unable to open socket"
#define ERR115_CONNECTION_REFUSED "(115) connection refused"
#define ERR116_UNABLE_TO_CONNECT "(116) unable to connect"
#define ERR117_LOCK_ERROR_EACCES "(117) lock error: EACCES"
#define ERR118_LOCK_ERROR_EEXIST "(118) lock error: EEXIST"
#define ERR119_LOCK_ERROR_EINVAL "(119) lock error: EINVAL"
#define ERR120_LOCK_ERROR_ENOENT "(120) lock error: ENOENT"
#define ERR121_LOCK_ERROR_ENOSPC "(121) lock error: ENOSPC"
#define ERR122_LOCK_ERROR_OTHER  "(122) lock error"
#define ERR123_BAD_ENV_HEADER "(123) bad environment header"
#define ERR124_BAD_STDIN_HEADER "(124) bad stdin header"

/* #define onError(s,x)    {estatus=s; emsg=x; goto error;} */


typedef struct resource_tag
{  
    char sw_info  [MAXSZ]; /* path to pcgi info file */
    char sw_name  [MAXSZ]; /* module name */
    char sw_home  [MAXSZ]; /* home path */
    char sw_exe   [MAXSZ]; /* path to executable, e.g. /usr/local/bin/python */
    char procpath [MAXSZ]; /* path to file containing pid */
    char sockpath [MAXSZ]; /* binding path for UNIX, Win32 named pipes */
    char pubpath  [MAXSZ]; /* path to pcgi_publisher.py(c) */
    int  sockport;         /* port number, if INET socket */
    char sockhost [MAXSZ]; /* hostname, if INET socket */
    char modpath  [MAXSZ]; /* module path */
    char errmsg   [MAXSZ]; /* last error, brief message */
    char errlog   [MAXSZ]; /* fully qualified path to error log file */
    char insertPath  [MAXPATH];  /* insert path by publisher */
    char pythonPath  [MAXPATH];  /* PYTHONPATH, if provided */
    short displayErrors;   /* displayErrors = 0,1 */
    long sz_env;
    long sz_input;
    long sz_output;
    long sz_error;
    char *p_env;
    char *p_input;
    char *p_output;
    char *p_error;
    int  procid;
    int  conn;
    int  lock;
} pcgiResource;

static char errorHtml[]=
"Status: %s\n"
"Content-Type: text/html\n"
"Pragma: nocache\n"
"Expires: Thu, 01 Dec 1994 16:00:00 GMT\n\n"
"<HTML>\n"
"<HEAD>\n"
"<TITLE>Temporarily Unavailable</TITLE>\n"
"</HEAD>\n"
"<BODY BGCOLOR=\"#FFFFFF\">\n"
"<TABLE BORDER=\"0\" WIDTH=\"100%%\">\n"
"<TR>\n"
"  <TD WIDTH=\"10%%\">\n"
"  <CENTER>\n"
"  <B><FONT SIZE=\"+6\" COLOR=\"#77003B\">!</FONT></B>\n"
"  </CENTER>\n"
"  </TD>\n"
"  <TD WIDTH=\"90%%\"><BR>\n"
"  <FONT SIZE=\"+2\">Temporarily Unavailable</FONT>\n"
"  <P>\n"
"  The resource you requested is temporarily unavailable - "
"please try again later.\n"
"  </TD>\n"
"</TR>\n"
"</TABLE>\n"
"%s\n"
"<!--\n%s\n%s\n-->\n"
"</BODY></HTML>";

/* To ensure backward compatibility with pcgi info files, */
/* don't change the order of the first 4 enum elements.   */
enum { resource_sockpath=0,
       resource_procpath=1,
       resource_workdir=2,
       resource_modpath=3, /* remaining elements not order dependent */
       resource_sockport,
       resource_sockhost,
       resource_exepath,
       resource_exefile,
       resource_pubpath,
       resource_ENUM };

/* Declarations */

void cleanup(void);
void onError(char *, char *, pcgiResource *);
int pcgiAssignPublisherPath(char *, pcgiResource *);
int pcgiPutEnvironment(char *);
long pcgiRead(pcgi_socket, char *, long);
long pcgiWrite(pcgi_socket, const char *, long);
int pcgiVerifyProc(pcgiResource *);
pcgi_socket pcgiConnect(pcgiResource *);
int pcgiStartProc(pcgiResource *);
int pcgiParseInfo(pcgiResource *);
int pcgiPutNameValueInEnvironment(char *, char *);
void pcgiSIG(int);
void pcgiPrintEnvironment();
void pcgiPrintResourceInfo(pcgiResource *);
int pcgiTruthValue(char);
#ifdef WIN32
void amendPathSeparators(char *);
long pcgiReadSocket(pcgi_socket, char *, long);
long pcgiWriteSocket(pcgi_socket, const char *, long);
#endif

#ifdef HAVE_UNION_SEMUN
#define UNION_SEMUN union semun
#else
#define UNION_SEMUN \
    union semun { \
        int val; \
        struct semid_ds *buf; \
        ushort *array; \
    } arg;
#endif

#define PCGI_H  1
#endif
