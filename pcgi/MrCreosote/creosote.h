/* creosote.h */

#include <stdlib.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <sys/types.h>

#define CREOSOTE_HOST  "127.0.0.1"
#define CREOSOTE_PORT  7739
#define spew(x) spewMrCreosote(x)

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
typedef int         creosote_socket;
typedef struct sockaddr_in SOCKADDR_IN;
#endif

#ifdef WIN32
#include <windows.h>
#include <iostream.h>
#include <winsock.h>
typedef SOCKET      creosote_socket;
#endif

struct MrCreosote
{
    char host[256];
    int port;
    creosote_socket socket;
    SOCKADDR_IN serv_addr;
};

/* Declarations */
void closeMrCreosote();
int initializeMrCreosote();
void spewMrCreosote(char *msg);
