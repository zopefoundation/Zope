/* creosote.c */

#include "creosote.h"

struct MrCreosote CreosoteServer;

void closeMrCreosote()
{
    struct MrCreosote *c = &CreosoteServer;
    if (c->socket)
    {
#ifdef UNIX
        close(c->socket);
#endif
#ifdef WIN32
        closesocket(c->socket);
        WSACleanup();
#endif
    }
    c->socket = 0;
}

#ifdef UNIX
int initializeMrCreosote()
{
    struct MrCreosote *c = &CreosoteServer;
    SOCKADDR_IN addr, *serv;
    creosote_socket *s;

    serv = &(c->serv_addr);
    s = &(c->socket);

    c->port = CREOSOTE_PORT;
    strcpy(c->host, CREOSOTE_HOST);

    bzero(serv, sizeof(*serv));
    serv->sin_family = AF_INET;
    serv->sin_addr.s_addr = inet_addr(c->host);
    serv->sin_port = htons(c->port);

    if ((*s = socket(AF_INET, SOCK_DGRAM, 0)) < 0)
    {
        return(-1);
    }

    bzero((char *) &addr, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(0);

    if (bind(*s, (struct sockaddr *) &addr, sizeof(addr)) < 0)
    {
        return(-1);
    }

    return(0);
}
#endif
#ifdef WIN32
int initializeMrCreosote()
{
    struct MrCreosote *c = &CreosoteServer;
    SOCKADDR_IN *serv;
    creosote_socket *s;
    WSADATA WsaData;
    int enable = 1;

    s = &(c->socket);

    if (!c->port)
    {
        c->port = CREOSOTE_PORT;
    }

    if (!c->host[0])
    {
        strcpy(c->host, CREOSOTE_HOST);
    }

    if (0 != WSAStartup(MAKEWORD(2,0), &WsaData))
    {
        return(-1);
    }

    /* Set the address */
    serv = &(c->serv_addr);
    serv->sin_family = AF_INET;
    serv->sin_addr.s_addr = inet_addr(c->host);
    serv->sin_port = htons((short)c->port);

    /* Create socket */
    *s = socket(AF_INET, SOCK_DGRAM, 0);
    if (INVALID_SOCKET == *s) { return(-1); }

    /* Permit the socket to broadcast */
    if (SOCKET_ERROR == setsockopt(*s, SOL_SOCKET, SO_BROADCAST, (char *) &enable, sizeof(enable)))
    {
        return(-1);
    }

    return(0);
}
#endif

void setMrCreosoteHost(char *host)
{
    /* 
       If not using localhost, setMrCreosoteHost() must be called
       before initializeMrCreosote(). 
    */
    strcpy(CreosoteServer.host, host);
}

void setMrCreosotePort(int port)
{
    /* must be done before initializeMrCreosote() is called */
    CreosoteServer.port = port;
}

void spewMrCreosote(char *msg)
{
    struct MrCreosote *c = &CreosoteServer;
    sendto(c->socket, msg, strlen(msg), 0, (struct sockaddr *) &(c->serv_addr), sizeof(c->serv_addr));
}

#if 0
int main(int argc, char *argv[])
{
    if ( (initializeMrCreosote()) < 0)
    {
        printf("initializeMrCreosote() failed\n");
        exit(1);
    }
    spew("Hello, world");
    closeMrCreosote();
    return(0);
}
#endif
