/* pcgi-wrapper.c - Persistent CGI wrapper module

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

|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
  - 2.0a5  29 October 1998
    - (brian) fixed arg type mismatch for semctl

  - 2.0a4  10 August 1998
    - (jeff) fixed Win32 local socket host address issues

  - 2.0a4  8 August 1998
    - (jeff) added Win32 support
*/
#include "pcgi.h"

#ifdef CREOSOTE
#include "creosote.h"  /* used for debugging */
char spewbuf[1024];    /* yes, it's a global, but only for debugging */
#endif

static char _id_[]="$Id: pcgi-wrapper.c,v 1.5 1998/12/03 22:43:03 brian Exp $";

/* Globals, OR: "I'll know I'll hate myself in the morning" */
extern char **environ;
int CloseFileDescriptors = 0;

#if UNIX
int g_lock = 0;
#endif

#if PCGI_WRAPPER_MAIN
int main(int argc, char *argv[])
{   pcgiResource resource;
    pcgiResource *r=&resource;
    long l       =0;
    char t[10]   ={0};
    char *estatus=NULL;
    char *emsg   =NULL;
    char *p      =NULL;
    char **env;

#ifdef CREOSOTE
    initializeMrCreosote();
    /* spew("pcgi-wrapper main()"); */
#endif

#ifdef CLOSE_FDS
    CloseFileDescriptors = 1;
#endif


    /*
    // Initialize resource info
    */
    memset(r,0,sizeof(pcgiResource));
    r->conn=-1;

    if (argc < 2) 
    {
        onError(E_500, "No pcgi info file given!", r);
    }

    strcpy(r->sw_info, argv[1]);
    if ((pcgiParseInfo(r)) < 0)
    {
        onError(E_500, "Error parsing pcgi info file", r);
    }

    /*
    // Copy environment to resource
    */
    for(env=environ; *env != 0; env++)
    {
        r->sz_env+=(strlen(*env)+sizeof(char));
    }
    if((r->p_env=malloc(((sizeof(char) * r->sz_env)+(sizeof(char)*HDRLEN))))==NULL)
    {
        onError(E_500, "Error allocating env", r);
    }
    p=r->p_env;
    sprintf(p, HDRFMT, r->sz_env);

    if (p[0] != '0')
    {
        if (!r->errmsg[0])
            strcpy(r->errmsg, ERR123_BAD_ENV_HEADER);
        onError(E_500, "Error allocating env", r);
    }

    p+=HDRLEN;
    for(env=environ; *env != 0; env++)
    {   l=strlen(*env);
        memcpy(p, *env, l);
        p+=l;
        *p=0;
        p++;
    }

    /*
    // Copy stdin to resource
    */
    p=getenv("CONTENT_LENGTH");
    if((p != NULL) && ((r->sz_input=atol(p)) > 0))
    {  
        if((r->p_input=malloc(((sizeof(char) * r->sz_input)+
                               (sizeof(char)*HDRLEN))))==NULL)
        {
            onError(E_500, "Error allocating stdin", r);
        }
        p=r->p_input;
        sprintf(p, HDRFMT, r->sz_input);

        if (p[0] != '0')
        {
            if (!r->errmsg[0])
                strcpy(r->errmsg, ERR124_BAD_STDIN_HEADER);
            onError(E_500, "Error allocating stdin", r);
        }

        p+=HDRLEN;
        if(pcgiRead(STDIN_FILENO, p, r->sz_input) != r->sz_input)
        {
            onError(E_500, "Error reading stdin", r);
        }
    }
    else
    {   
        if((r->p_input=malloc(sizeof(char)*HDRLEN))==NULL)
        {
            onError(E_500, "Error allocating stdin", r);
        }
        sprintf(r->p_input, HDRFMT, 0);
    }

    /*
    // Attempt to connect
    */
    if ((r->conn = pcgiConnect(r)) < 0)
    {   
        if(pcgiVerifyProc(r) < 0)
        {   
            if(pcgiStartProc(r) < 0) 
            {
                if (!r->errmsg[0])
                    strcpy(r->errmsg, ERR101_FAILURE_DURING_START); 
                onError(E_500, "Failed to start resource", r);
            }
            if ((r->conn=pcgiConnect(r)) < 0)
            {
                if (!r->errmsg[0])
                    strcpy(r->errmsg, ERR102_FAILURE_DURING_CONNECT); 
                onError(E_503, strerror(errno), r);
            }
        }
        else
        {   
            if (!r->errmsg[0])
                strcpy(r->errmsg, ERR103_UNABLE_VERIFY_RUNNING);
            onError(E_503, "pcgiVerifyProc failed", r);
        }
    } 

    /*
    // Send environment and stdin
    */
#ifdef WIN32
    if (pcgiWriteSocket(r->conn,r->p_env,(r->sz_env+HDRLEN)) != (r->sz_env+HDRLEN))
#endif
#ifdef UNIX
    if (pcgiWrite(r->conn,r->p_env,(r->sz_env+HDRLEN)) != (r->sz_env+HDRLEN))
#endif
    {
        if (!r->errmsg[0])
            strcpy(r->errmsg, ERR104_ENVIRONMENT_SEND);
        onError(E_500, "Error sending env", r);
    }

#ifdef WIN32
    if (pcgiWriteSocket(r->conn,r->p_input,(r->sz_input+HDRLEN)) != (r->sz_input+HDRLEN))
#endif
#ifdef UNIX
    if (pcgiWrite(r->conn,r->p_input,(r->sz_input+HDRLEN)) != (r->sz_input+HDRLEN))
#endif

    {
        if (!r->errmsg[0])
            strcpy(r->errmsg, ERR105_STDIN_SEND);
        onError(E_500, "Error sending stdin", r);
    }

#ifdef WIN32
shutdown(r->conn, 1); /* shutdown the socket so we can receive */
#endif

    /*
    // Receive stdout and stderr
    */
    t[0]='\0';
#ifdef WIN32
    if (!pcgiReadSocket(r->conn, t, HDRLEN))
#endif
#ifdef UNIX
    if (!pcgiRead(r->conn, t, HDRLEN))
#endif
    {
        if (!r->errmsg[0])
            strcpy(r->errmsg, ERR106_STDOUT_READ_HEADER);
        onError(E_503, strerror(errno), r);
    }

    if (strlen(t) <= 0)
    {
        if (!r->errmsg[0])
            sprintf(r->errmsg, "%s (%d)", ERR107_BAD_STDOUT_STRLEN, strlen(t));
       onError(E_503, strerror(errno), r);
    }

    if (t[0] != '0')
    {
      /* XXX - Later: process this as out-of-bound stdin data */
        sprintf(r->errmsg, "t[0] = %d", (int) t[0]);
        onError(E_500, "unexpected out-of-bound data in stdin", r);
    }
    else
    {
        r->sz_output=atol(t);
        l=(sizeof(char) * r->sz_output) + sizeof(char);
        r->p_output=(char *)malloc(l);
        memset(r->p_output,0,l);
#ifdef WIN32
        if (pcgiReadSocket(r->conn,r->p_output,r->sz_output) != r->sz_output)
#endif
#ifdef UNIX
        if (pcgiRead(r->conn,r->p_output,r->sz_output) != r->sz_output)
#endif
        {
            if (!r->errmsg[0])
                strcpy(r->errmsg, ERR108_STDOUT_READ_BODY);
            onError(E_500, "Error receiving stdout", r);
        }
    }

    t[0]='\0';
#ifdef WIN32
    if (!pcgiReadSocket(r->conn, t, HDRLEN))
#endif
#ifdef UNIX
    if (!pcgiRead(r->conn, t, HDRLEN))
#endif
    {
        if (!r->errmsg[0])
            strcpy(r->errmsg, ERR109_STDERR_READ_HEADER);
        onError(E_500, "Error receiving stderr size", r);
    }
    if (strlen(t) <= 0)
    {
        if (!r->errmsg[0])
            sprintf(r->errmsg, "%s (%d)", ERR110_BAD_STDERR_STRLEN, strlen(t));
        onError(E_500, "Error receiving stderr size", r);
    }

    if (t[0] != '0')
    {
      /* XXX - Later: process this as out-of-bound stderr data */
        sprintf(r->errmsg, "t[0] = %d", (int) t[0]);
        onError(E_500, "unexpected out-of-bound data in stderr", r);
    }
    else
    {
        r->sz_error=atol(t);
        if (r->sz_error > 0)
        {   
            l=(sizeof(char) * r->sz_error) + sizeof(char);
            r->p_error=(char *)malloc(l);
            memset(r->p_error,0,l);
#ifdef WIN32
            if (pcgiReadSocket(r->conn, r->p_error, r->sz_error) != r->sz_error)
#endif
#ifdef UNIX
            if (pcgiRead(r->conn, r->p_error, r->sz_error) != r->sz_error)
#endif
            {
                if (!r->errmsg[0])
                    strcpy(r->errmsg, ERR111_STDERR_READ_BODY);
                onError(E_500, "Error receiving stderr", r);
            }
        }
    }
#ifdef UNIX
    close(r->conn);
#endif
#ifdef WIN32
    closesocket(r->conn);
#endif

    /*
    // Return stdout and stderr to server
    */
    if (r->sz_output != 0)
    {
        if (pcgiWrite(STDOUT_FILENO,r->p_output,r->sz_output) != r->sz_output)
        {
            if (!r->errmsg[0])
                strcpy(r->errmsg, "(112) Error returning stdout to server"); 
            onError(E_500, ERR112_STDOUT_TO_SERVER, r);
        }
        free(r->p_output);
        r->p_output=NULL;
    }

    if (r->sz_error != 0)
    {   
        if (pcgiWrite(STDERR_FILENO,r->p_error,r->sz_error) != r->sz_error)
        {
            if (!r->errmsg[0])
                strcpy(r->errmsg, ERR113_STDOUT_TO_SERVER);
            onError(E_500, "Error returning stderr", r);
        }
        free(r->p_error);
        r->p_error=NULL;
    }

    /*
    // Free env & input buffers, release lock if needed
    */
    free(r->p_env);
    r->p_env=NULL;
    free(r->p_input);
    r->p_input=NULL;
    cleanup();
    fflush(stdout);
    fflush(stderr);
    /*exit(0);*/
    return 0;
}
#endif /* end of main(): PCGI_WRAPPER_MAIN */

/*
// onError: fatal pcgi error
 */
void onError(char *estatus, char *emsg, pcgiResource *r)
{
    FILE *f;
    time_t now;
#ifdef VERSION
    /* If VERSION isn't defined as a string, everything will blow up here
       during compilation. */
    char *pcgi_version="pcgi-wrapper-version " VERSION;
#else
    char *pcgi_version = "";
#endif
    char *displayError = "";

    if (r != NULL)
    {
#ifdef UNIX
        if(r->conn != -1)    close(r->conn);
        cleanup();
#endif
#ifdef WIN32
        if (r->conn)
        {
            shutdown(r->conn, 1);
            closesocket(r->conn);
            WSACleanup();
        }
#endif
        if (r->errlog[0])
        {   
            if((f=fopen(r->errlog, "ab")) != NULL)
            {
                now = time(NULL); 
                fprintf(f, "%s  pcgi-wrapper: %s  %s\n", 
                        ctime(&now), emsg, r->errmsg);
                fclose(f);
            }
        }

        if(r->p_env!=NULL)   free(r->p_env);
        if(r->p_input!=NULL) free(r->p_input);
    }
    if (r->displayErrors)
      displayError = r->errmsg;
    printf(errorHtml, estatus, displayError, emsg, pcgi_version);
    fflush(stdout);
    fflush(stderr);

    exit(0);
}

/*
// pcgiWrite: write n bytes to a an fd
*/
long pcgiWrite(pcgi_socket fd, const char *ptr, long nbytes)
{   
    long done    = 0;
    long notdone = nbytes;
    const char *cptr = (const char *)ptr;

    while (notdone > 0)
    {   
        done = write(fd, cptr, notdone);
        if (done <= 0) 
        {
            return (done);
        }
        notdone -= done;
        cptr += done;
    }
    return ((nbytes - notdone));
}

#ifdef WIN32
long pcgiWriteSocket(pcgi_socket fd, const char *ptr, long nbytes)
{
    /* The successful completion of a send does not indicate */
    /* that the data was successfully delivered.  */
    int count;
    int req;
    long bytesSent = 0;

/* begin superKludge(tm) - only for testing, do not leave in place XXX */
/*     if (STDOUT_FILENO == (int)fd) */
/*     { */
/*         printf("%s", ptr); */
/*         return 0; */
/*     } */
/* end superKludge(tm) - only for testing, do not leave in place XXX */

    while ( bytesSent < nbytes )
    {
        req = nbytes - bytesSent;
        count = send(fd, ptr + bytesSent, req, 0);
        if (SOCKET_ERROR == count)
        {
            return(-1);
        }
        bytesSent += (long) count;
    }

    return(bytesSent);
}
#endif

/*
// pcgiRead: read n bytes from an fd
*/
long pcgiRead(pcgi_socket fd, char *ptr, long n)
{   
    long done    = 0;
    long notdone = n;
    char *cptr   = ptr;

    while (notdone > 0)
    {   
        done = read(fd, cptr, notdone);
        if (done < 0)       
            return (done);   /* ERROR */
        else if (done == 0) 
            break;           /*  EOF  */
        notdone -= done;
        cptr += done;
    }
    return ((n - notdone));
}

#ifdef WIN32
long pcgiReadSocket(pcgi_socket fd, char *ptr, long nbytes)
{
    int count;
    int req;
    long bytesRecv = 0;

    while ( bytesRecv < nbytes )
    {
        req = nbytes - bytesRecv;
        count = recv(fd, ptr + bytesRecv, req, 0);
        if (SOCKET_ERROR == count)
        {
            /* TODO: add error reporting by calling WSAGetLastError */
            return(-1);
        }
        bytesRecv += (long) count;
    }
    return(bytesRecv);
}
#endif

/*
// pcgiVerifyProc: check to see if a resource is running
*/
int pcgiVerifyProc(pcgiResource *r)
{   FILE *f;
    char p[10];

    memset(p,0,10);
    if (r->procid == 0)
    {   if((f=fopen(r->procpath, "r")) == NULL)
            return(-1);
        if(fgets(p, HDRLEN, f) == NULL)
            return(-1);
        fclose(f);
        if(!(strlen(p) > 0))
            return(-1);
        r->procid=atoi(p);
    }
#ifdef UNIX
   return(kill(r->procid, 13));
#endif
#ifdef WIN32
    if ((NULL == OpenProcess(PROCESS_VM_READ, FALSE, r->procid)))
    {
        return(-1);
    }
    return(0);
#endif
}

/*
// pcgiConnect: return fd of a connected socket
*/
#ifdef UNIX
pcgi_socket pcgiConnect(pcgiResource *r)
{   
    struct sockaddr_un s;
    pcgi_socket fd;
    int addrlen=0;
    int connected=-1;
    int attempted=0;
    int retry=10;
    int delay=1;

    memset((char *) &s, 0, sizeof(s));
    s.sun_family=AF_UNIX;
    strcpy(s.sun_path, r->sockpath);

    addrlen = sizeof(struct sockaddr_un);  /* force to use sizeof(s) */

    if ((fd = socket(AF_UNIX, SOCK_STREAM, 0)) < 0)
    {
        if (!r->errmsg[0])
            strcpy(r->errmsg, ERR114_UNABLE_TO_OPEN_SOCKET);
        return (-1);
    }
    while ((connected < 0) && (attempted <= retry))
    {   
        if ((connected=connect(fd, (struct sockaddr *) &s, addrlen)) < 0)
        {   
            if((errno!=ECONNREFUSED) && (errno!=ENOENT))
            {   
                if (!r->errmsg[0])
                    strcpy(r->errmsg, ERR115_CONNECTION_REFUSED);
                return(-1);
            }
            sleep(delay);
            attempted++;
        }
    }
    if (!(connected < 0)) 
    {
        if (!r->errmsg[0])
            sprintf(r->errmsg, "%s, fd=%d", ERR116_UNABLE_TO_CONNECT, fd);
        return (fd);
    }
    return (connected);
}
#endif  /* UNIX pcgiConnect */


#ifdef WIN32
pcgi_socket pcgiConnect(pcgiResource *r)
{
    pcgi_socket destSocket;
    SOCKADDR_IN destSockAddr;
    unsigned long destAddr;
    int connected = SOCKET_ERROR;
    int attempted = 0;
    int status;
    WSADATA WsaData;

    char hostName[MAXSZ];
    LPHOSTENT hostEnt;
    SOCKADDR_IN hostAddr;

    /* initialize the Windows Socket DLL */
    /* TODO: move this startup code outside of pcgiConnect */
    if (0 != WSAStartup(MAKEWORD(2, 0), &WsaData))
    {
        return(-1);
    }

    /* destAddr = inet_addr("192.168.2.43"); */
    hostAddr.sin_addr.s_addr = INADDR_ANY;  /* init local address */

    /*  Bug: assumes r->sockhost is the host name, we should also
        check to see if it is the xxx.xxx.xxx.xxx octet string and
        act accordingly */

    if (r->sockhost[0])
        strcpy(hostName, r->sockhost);
    else if (SOCKET_ERROR == gethostname(hostName, MAXSZ))
        return(-1);
    hostEnt = gethostbyname((LPSTR) hostName);
    if (hostEnt)
    {
        /* resolve hostname for local address */
        hostAddr.sin_addr.s_addr = *((u_long FAR*) (hostEnt->h_addr));
    }
    if (INADDR_ANY == hostAddr.sin_addr.s_addr)
    {
        return(-1);
    }
    destAddr = hostAddr.sin_addr.s_addr;

    memcpy(&destSockAddr.sin_addr, &destAddr, sizeof(destAddr));
    destSockAddr.sin_port = htons((short)r->sockport);
    destSockAddr.sin_family = AF_INET;

    /* create socket */
    destSocket = socket(AF_INET, SOCK_STREAM, 0);
    if (INVALID_SOCKET == destSocket)
    {
        return(-1);
    }

    /* Connect */
    /*     The code below blithely duplicates the Unix version. */
    /*     TODO:  add better recovery/error handling. */

    while ((SOCKET_ERROR == connected) && (attempted <= CONNRETRY))
    {
        connected = connect(destSocket, (LPSOCKADDR) &destSockAddr, sizeof(destSockAddr));

        if (SOCKET_ERROR == connected)
        {
            status = WSAGetLastError();
            if ((status != WSAECONNREFUSED) && (status != ENOENT))
            {
                return(-1);
            }
            sleep(CONNDELAY);
            attempted++;
        }
    }
    if (SOCKET_ERROR == connected)
    {
        closesocket(destSocket);
        WSACleanup();
        return(-1);
    }

    return(destSocket);
}
#endif  /* Win32 pcgiConnect */


#ifdef UNIX
static sig_atomic_t sigflag;
static sigset_t nmask, omask, zmask;
#endif

#ifdef UNIX
void pcgiSIG(int s)
{   
    sigflag=1; 
    return;
}
#endif

void cleanup()
{   
#ifdef UNIX
    UNION_SEMUN arg;
    arg.val=0;
    if (g_lock > 0) 
    {
        semctl(g_lock, 1, IPC_RMID, arg);
    }
#endif
}

/*
// pcgiStartProc: manages starting a pcgi resource.
*/
#ifdef UNIX
int pcgiStartProc(pcgiResource *r)
{   
    pid_t pid;
    char  *p = NULL;
    int   i = 0;
    UNION_SEMUN arg;
    arg.val=0;

    if ((p=strrchr(r->sw_exe, PATHSEP))==NULL)
    {   
        p = r->sw_exe;
    }
    else
    {   
        p++;
    }

    /* Set up signal handlers to coordinate timing */
    signal(SIGUSR1, pcgiSIG);
    signal(SIGUSR2, pcgiSIG);
    sigemptyset(&zmask);
    sigemptyset(&nmask);
    sigaddset(&nmask, SIGUSR1);
    sigaddset(&nmask, SIGUSR2);
    sigprocmask(SIG_BLOCK, &nmask, &omask);

    /* Make sure another wrapper isn't already doing a restart */
    if ((r->lock=semget(101, 1, 0700 | IPC_CREAT | IPC_EXCL)) == -1)
    {
        if (errno == EACCES)
            strcpy(r->errmsg, ERR117_LOCK_ERROR_EACCES);
        else if (errno == EEXIST)
            strcpy(r->errmsg, ERR118_LOCK_ERROR_EEXIST);
        else if (errno == EINVAL)
            strcpy(r->errmsg, ERR119_LOCK_ERROR_EINVAL);
        else if (errno == ENOENT)
            strcpy(r->errmsg, ERR120_LOCK_ERROR_ENOENT);
        else if (errno == ENOSPC)
            strcpy(r->errmsg, ERR121_LOCK_ERROR_ENOSPC);
        else
            sprintf(r->errmsg, "%s, %d", ERR122_LOCK_ERROR_OTHER, errno);
        return(-1);
    }

    /* Keep us from dying without cleaning up our semaphore by
       setting signal handlers to ensure that the sem will always
       be released. We don't set handlers for SIGUSR1 SIGUSR2 or
       SIGCHLD, because we need those to coordinate with the child
       process(es) that we fork. */
    g_lock = r->lock;

    for(i=0; i<32; i++)
    {   
        if ((i!=SIGUSR1) && (i!=SIGUSR2) && (i != SIGCHLD))
        {
            signal(i, (void *)cleanup);
        }
    }

    /* If the old socket file exists and we have write permission,
       attempt to remove it. */
    if (r->sockport == 0 && access(r->sockpath, W_OK) == 0)
    {
        unlink(r->sockpath);
    }

    /* Fork a child which forks a child -- this is so that
       init will inherit the grandchild (so it won't die) */
    if ((pid = fork()) < 0)
    {   
        semctl(r->lock, 1, IPC_RMID, arg);
        return(-1);
    }
    else if (pid == 0)
    {   
        if ((pid = fork()) < 0) 
        {
            return(-1);
        }
        else if (pid > 0)
        {   /* Let child know we're going away so it can start */
            kill(pid, SIGUSR1);
            exit(0);
        }

        setsid();
        chdir("/");

        /* Wait for parent to go away */
        while(sigflag == 0) 
            sigsuspend(&zmask);
        sigflag = 0;
        sigprocmask(SIG_SETMASK, &omask, NULL);

        /* Platform oddities... */
        if (CloseFileDescriptors)
        {
            close(STDIN_FILENO);
            close(STDOUT_FILENO);
            close(STDERR_FILENO);
        }

        execl(r->sw_exe,
              p,
              r->pubpath,
              (char *)0);
        exit(0);           
    }

    /* Wait for the first child to finish */
    if (waitpid(pid, NULL, 0) < 0)
    {   semctl(r->lock, 1, IPC_RMID, arg);
        return(-1);
    }

    /*
    // Release restart lock!
    */
    semctl(r->lock, 1, IPC_RMID, arg);

    /*
    // Reset signal handlers
    */
    for(i=0; i<10; i++) 
    {
        signal(i, SIG_DFL);
    }

    sleep(2);
    return (0);
}
#endif  /* UNIX pcgiStartProc */

#ifdef WIN32
int pcgiStartProc(pcgiResource *r)
{
    HANDLE mutex = 0;
    char pythonExecutable[256];
    char command_line[1024];
    BOOL createProcessStatus;
    STARTUPINFO StartupInfo;
    PROCESS_INFORMATION ProcessInfo;
    int waitStatus;

    GetStartupInfo(&StartupInfo);

    /* Is another wrapper attempting a restart? */
    mutex = CreateMutex(NULL, FALSE, MUTEX_NAME);
    if (NULL == mutex)
    {
        //TODO: add error reporting
        return(-1);
    }

    waitStatus = WaitForSingleObject(mutex, (AUTODELAY * 1000));
    if (WAIT_TIMEOUT == waitStatus)
    {
        //TODO: add error reporting
        return(-1);
    }
    else if (WAIT_FAILED == waitStatus)
    {
        //TODO: add error handling by calling GetLastError()
        return(-1);
    }

    /*
    Travel beyond this point requires calling the
    ReleaseMutex function.  Fortunately, the Win32
    mutex is automatically released when a process
    terminates, but we could still encounter a
    situation where the process is hung or stalled ...
    */

  if (r->sw_exe[0])
      strcpy(pythonExecutable, r->sw_exe);
  else
    strcpy(pythonExecutable, "python");

    sprintf(command_line, "%s %s", pythonExecutable, r->pubpath);

    createProcessStatus = CreateProcess(
        NULL,
        command_line,
        NULL,
        NULL,
        FALSE,
        DETACHED_PROCESS,
        NULL,
        NULL,
        &StartupInfo,
        &ProcessInfo);

     /* wait a little bit to give the published
     application enough time to initialize itself */

//Yech!!!
    sleep(AUTODELAY); // <<<-- use a ReadySignal(tm), if available :)

    ReleaseMutex(mutex);
    CloseHandle(mutex);

    if (0 == createProcessStatus)
    {
        //TODO: report more information about failure
        return(-1);
    }
    else
    {
        r->procid = ProcessInfo.dwProcessId; /* assign process id */
        return(0);
    }
}
#endif
