/* parseinfo.c - module to parse the pcgi info file

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

#include "pcgi.h"

extern char **environ;
extern int CloseFileDescriptors;

int pcgiAssignCloseFileDescriptors(pcgiResource *r, char *val)
{
    if ((CloseFileDescriptors = pcgiTruthValue(val[0]) < 0))
    {
        sprintf(r->errmsg, "unknown value for PCGI_CLOSE_FDS: %s", val);
        return(-1);
    }
    return(0);
}

int pcgiAssignPublisher(pcgiResource *r)
{
    /*
    // Determine the publisher path based on the current values
    // of the pcgiResource structure.
    */
    char *p, *pBegin, *pEnd, testdir[MAXSZ];
    char combinedPaths[MAXPATH+MAXPATH+2];

    if (r->pubpath[0]) /* assignment already made, our work is done :) */
    {
        return(0);
    }
    /*
    //  Look through the PCGI_INSERT_PATH directories for the publisher.
    */
    strcat(combinedPaths, r->insertPath);
    strcat(combinedPaths, ":");
    strcat(combinedPaths, r->pythonPath);

    pBegin = combinedPaths;
    pEnd = pBegin + strlen(combinedPaths);
    while(pBegin < pEnd)
    {
        p = pBegin;
        do {
            if (*p == ':' || *p == '\0')
                break;
        } while(*p++);
        strncpy(testdir, pBegin, p-pBegin);
        testdir[p-pBegin] = '\0';
        if ((pcgiAssignPublisherPath(testdir, r))==0)
        {
            return(0);
        }
        if (p == pBegin) 
        {
            pBegin++;
        }
        else
        {
            pBegin = p; 
        }
    }

    /*
    //  Run through a gauntlet of misc. attempts to find the publisher.
    */
    if (r->modpath[0])
    {
        if ((pcgiAssignPublisherPath(r->modpath, r)) == 0)
            return(0);
    }
    if (r->sw_info[0])
    {
        if ((pcgiAssignPublisherPath(r->sw_info, r)) == 0)
            return(0);
    }
    if (r->sw_home[0])
    {
        if ((pcgiAssignPublisherPath(r->sw_home, r)) == 0)
            return(0);
    }
    if (r->sw_exe[0])
    {
        if ((pcgiAssignPublisherPath(r->sw_exe, r)) == 0)
            return(0);
    }
    return(-1);
}

#define PubCount 4  /* variations on a publisher name */

int pcgiAssignPublisherPath(char *path, pcgiResource *r)
{
    /*
    // Attempt to assign the path to the publisher, return 0 for success,
    // otherwise -1.
     */
    char *p[PubCount];
    char testdir[MAXSZ], pubpath[MAXSZ];
    int i, len;
    struct stat statbuf;

    p[0] = PUBLISHER_NAME_1;
    p[1] = PUBLISHER_NAME_2;
    p[2] = PUBLISHER_NAME_3;
    p[3] = PUBLISHER_NAME_4;

    strcpy(testdir, path); 
    len = strlen(testdir);
    if (len < 1 || (MAXSZ <= len + strlen(PUBLISHER_NAME_1) + 1))
    {
        return(-1);
    }
    if (PATHSEP == testdir[len-1]) 
    { 
        testdir[len-1] = '\0'; /* truncate trailing slash */
    }

    if (stat(testdir, &statbuf) == -1)
    {
        return(-1); /* unable to stat path */
    }

    if (!(statbuf.st_mode & S_IFDIR))
    {
        /* 
        // If the supplied path was not a directory, assume it was
        // a file and get the directory portion of it.
        */
        while(len > 0)
        {
            if (PATHSEP == testdir[--len])
            {
               testdir[len] = '\0';
               break;
            }
        }
        if (len < 1) { return(-1); }
    }

    for (i=0; i < PubCount; i++)
    {
        sprintf(pubpath, "%s%c%s", testdir, PATHSEP, p[i]);
        if (stat(pubpath, &statbuf) != -1)
        {
            if (statbuf.st_mode & S_IREAD)
            {
                strcpy(r->pubpath, pubpath);
                return(0);
            } 
        }
    }
    return(-1);
}

int pcgiEnvironmentToResourceAssignment(pcgiResource *r)
{
    /*
    // Read in the environment and make whatever appropriate assignments
    // prior to reading in the pcgi info file.  Values from the pcgi info
    // override environment settings.
    //
    // This function is necessary because the user may want to set
    // an enviroment variable globally (e.g. PCGI_PUBLISHER from 
    // a httpd .conf file),
    */
    char **env;
    char *p = NULL;
    char buf[MAXSZ];
    char *nam, *val;

    for (env=environ; *env != 0; env++)
    {
        if (strlen(*env) >= MAXSZ)
        {
            continue;
        }
        strcpy(buf, *env);

        if ((p = strchr(buf,'=')) != NULL)
        {
            *p++ = '\0';
            nam = buf;
            val = p;
            if((strncmp(nam, "SOFTWARE_", strlen("SOFTWARE_")))==0)
            {
                if((strcmp(nam,"SOFTWARE_NAME"))==0)
                    strcpy(r->sw_name, val);
                else if((strcmp(nam,"SOFTWARE_HOME"))==0)
                    strcpy(r->sw_home, val);
                else if((strcmp(nam,"SOFTWARE_EXE"))==0)
                    strcpy(r->sw_exe, val);
            }
            if((strcmp(nam,"PYTHONPATH"))==0)
            {
                /* TODO: check strlen against MAXPATH */
                strcpy(r->pythonPath, val);
            }
            else if((strncmp(nam, "PCGI_", strlen("PCGI_")))==0)
            {
                if ((strcmp(nam,"PCGI_CLOSE_FDS"))==0)
                {
                    if ((pcgiAssignCloseFileDescriptors(r, val)) < 0)
                        return(-1);
                }
                else if ((strcmp(nam,"PCGI_DISPLAY_ERRORS"))==0)
                      r->displayErrors = pcgiTruthValue(val[0]);
                else if ((strcmp(nam,"PCGI_ERROR_LOG"))==0)
                    strcpy(r->errlog, val);
                else if ((strcmp(nam,"PCGI_EXE"))==0)
                    strcpy(r->sw_exe, val);
                else if ((strcmp(nam,"PCGI_HOST"))==0)
                    strcpy(r->sockhost, val);
                else if ((strcmp(nam,"PCGI_INSERT_PATH"))==0 ||
                         (strcmp(nam,"PCGI_WORKING_DIR"))==0)
                {
                    if (strlen(val) >= MAXPATH)
                    {
                        strcpy(r->errmsg, "pcgiEnvironmentToResourceAssignment() length exceeds MAXPATH");
                        return(-1);
                    }
                    strcpy(r->insertPath, val);
                }
                else if ((strcmp(nam,"PCGI_MODULE_PATH"))==0)
                    strcpy(r->modpath, val);
                else if ((strcmp(nam,"PCGI_NAME"))==0)
                    strcpy(r->sw_name, val);
                else if ((strcmp(nam,"PCGI_PID_FILE"))==0)
                    strcpy(r->procpath, val);
                else if ((strcmp(nam,"PCGI_PORT"))==0)
                    r->sockport = atoi(val);
                else if ((strcmp(nam,"PCGI_PUBLISHER"))==0)
                    strcpy(r->pubpath, val);
                else if ((strcmp(nam,"PCGI_SOCKET_FILE"))==0)
                    strcpy(r->sockpath, val);
            }
        }
    }

    return(0);
}

/*
// pcgiParseInfo: Parse info file named in resource->sw_info
*/
int pcgiParseInfo(pcgiResource *r)
{   
    FILE *f;
    char buf[256];
    char *v=NULL;
    char *p=NULL;
    struct stat statbuf;
    int _newStyleDirectives = 0;
    int _oldStyleLineCount = 0;
    enum { oldStyleSocketFile, oldStyleProcessIdFile, oldStyleWorkDir, oldStyleModPath };

    if ((pcgiEnvironmentToResourceAssignment(r)) < 0)
    {
        if (!r->errmsg[0])
            strcpy(r->errmsg, "pcgiEnvironmentToResourceAssignment() error");
        return(-1);
    }

    if((f=fopen(r->sw_info, "r")) == NULL)
    {
        sprintf(r->errmsg, "unable to open info file: %s", r->sw_info);
        return(-1);
    }

    pcgiPutNameValueInEnvironment("PCGI_INFO_FILE", r->sw_info);

    while(fgets(buf, 255, f) != NULL)
    {   
      /* XXX - TODO: trim leading, trailing whitespace */

#ifdef WIN32
        amendPathSeparators(buf);
#endif
        if((buf[0] != '#') && (buf[0] != '\n'))
        {   
            p=(strrchr(buf,'\0')-sizeof(char));
            while((p >= buf) && (isspace(*p)))
            {  
                *p=0;
                p--;
            }

            if ((p=strchr(buf,'=')) != NULL)
            {
                _newStyleDirectives = 1;
                if ((pcgiPutEnvironment(buf) < 0))
                {
                    strcpy(r->errmsg, "pcgiPutEnvironment() failed");
                    fclose(f);
                    return(-1);
                }

                *p=0;
                p++;

                if((strcmp(buf,"SOFTWARE_NAME"))==0)
                {  
                    strcpy(r->sw_name, p);
                }
                else if((strcmp(buf,"SOFTWARE_HOME"))==0)
                {  
                    strcpy(r->sw_home, p);
                }
                else if((strcmp(buf,"SOFTWARE_EXE"))==0)
                {  
                    strcpy(r->sw_exe, p);
                }
                else if((strcmp(buf,"PCGI_CLOSE_FDS"))==0)
                {
                    if ((pcgiAssignCloseFileDescriptors(r, p)) < 0)
                        return(-1);
                }
                else if ((strcmp(buf,"PCGI_DISPLAY_ERRORS"))==0)
                    r->displayErrors = pcgiTruthValue(p[0]);
                else if((strcmp(buf,"PCGI_ERROR_LOG"))==0)
                {  
                    strcpy(r->errlog, p);
                }
                else if((strcmp(buf,"PCGI_EXE"))==0)
                {  
                    strcpy(r->sw_exe, p);
                }
                else if((strcmp(buf,"PCGI_HOST"))==0)
                {  
                    strcpy(r->sockhost, p);
                }
                else if((strcmp(buf,"PCGI_INSERT_PATH"))==0)
                {  
                    strcpy(r->insertPath, p);
                }
                else if((strcmp(buf,"PCGI_MODULE_PATH"))==0)
                {  
                    strcpy(r->modpath, p);
                }
                else if((strcmp(buf,"PCGI_NAME"))==0)
                {  
                    strcpy(r->sw_name, p);
                }
                else if((strcmp(buf,"PCGI_PID_FILE"))==0)
                {  
                    strcpy(r->procpath, p);
                }
                else if((strcmp(buf,"PCGI_PORT"))==0)
                {
                    r->sockport = atoi(p);
                }
                else if((strcmp(buf,"PCGI_PUBLISHER"))==0)
                {  
                    strcpy(r->pubpath, p);
                }
                else if((strcmp(buf,"PCGI_SOCKET_FILE"))==0)
                {  
                    strcpy(r->sockpath, p);
                }
                else if((strcmp(buf,"PCGI_WORKING_DIR"))==0)
                {  
                    strcpy(r->insertPath, p);
                }
                else if((strcmp(buf,"PYTHONPATH"))==0)
                {  
                    strcpy(r->pythonPath, p);
                }

            }
            else /* old-style (deprecated) directives */
            {
                /* assume old style where the first four lines correspond to */
                /* 1. path of the socket file */
                /* 2. path of the process id file */
                /* 3. working directory (to be added to path by publisher) */
                /* 4. path of the module to be published */
                if (_newStyleDirectives)
                {
                    strcpy(r->errmsg, "pcgi info file mixes old and new style directives (new style uses name=value)");
                    fclose(f);
                    return(-1);
                }
                if (oldStyleSocketFile == _oldStyleLineCount)
                {
                    strcpy(r->sockpath, buf);
                    pcgiPutNameValueInEnvironment("PCGI_SOCKET_FILE", buf);
                }
                else if (oldStyleProcessIdFile == _oldStyleLineCount)
                {
                    strcpy(r->procpath, buf);
                    pcgiPutNameValueInEnvironment("PCGI_PID_FILE", buf);
                }
                else if (oldStyleWorkDir == _oldStyleLineCount)
                {
                    strcpy(r->insertPath, buf);
                    if ((pcgiPutNameValueInEnvironment("PCGI_INSERT_PATH", buf)) < 0)
                    {
                        strcpy(r->errmsg, "pcgiPutNameValueInEnvironment() error");
                        fclose(f);
                        return(-1);
                    }
                }
                else if (oldStyleModPath == _oldStyleLineCount)
                {
                    strcpy(r->modpath, buf);
                    if ((pcgiPutNameValueInEnvironment("PCGI_MODULE_PATH", buf)) < 0)
                    {
                        strcpy(r->errmsg, "pcgiPutNameValueInEnvironment() error");
                        fclose(f);
                        return(-1);
                    }
                }
                else
                {
                    strcpy(r->errmsg, "oldStyleLineCount exceeds maximum");
                    fclose(f);
                    return(-1);
                }
                _oldStyleLineCount++;
            }     
        }
    }
    fclose(f);

    /* 
    //  Post-parsing work: decide if we have enough info to make it work. 
    */

    /*
    //  If the location of the publisher was not specified, try to
    //  locate it.
    */
    if (!r->pubpath[0])
    {
        pcgiAssignPublisher(r);
    }

    if (!r->pubpath[0])
    {
        strcpy(r->errmsg, "unable to determine the publisher location");
        return(-1);
    }
    else
    {
        if (stat(r->pubpath, &statbuf) == -1)
        {
            sprintf(r->errmsg, "missing publisher: %s", r->pubpath);
            return(-1);
        }
        else
        {
            if (!(statbuf.st_mode & S_IREAD))
            {
                sprintf(r->errmsg, "publisher read error: %s", r->pubpath);
                return(-1);
            }
        }
    }

    /*
    //  Assign defaults, where necessary, for backward compatibility.
    */
    if (r->sw_name[0] && r->sw_home[0])
    {
        if (!r->sw_exe[0])
        {
            strcpy(r->sw_exe,"/usr/local/bin/python1.4");
            pcgiPutNameValueInEnvironment("SOFTWARE_EXE", r->sw_exe);
        }
        if (!r->procpath[0])
        {
            sprintf(r->procpath,"%s/var/%s.pid", r->sw_home,r->sw_name);
            pcgiPutNameValueInEnvironment("PCGI_PID_FILE", r->procpath);
        }
        if (!r->sockpath[0])
        {
            sprintf(r->sockpath,"%s/var/%s.soc", r->sw_home,r->sw_name);
            pcgiPutNameValueInEnvironment("PCGI_SOCKET_FILE", r->sockpath);
        }
    }

    /*
    // Other than r->pubpath, the other required attributes to complete
    // the process are: r->procpath & r->sockpath.
    */
    if (!r->sockpath[0])
    {
        strcpy(r->errmsg, "missing parameter: PCGI_SOCKET_FILE");
        return(-1);
    }
    if (!r->procpath[0])
    {
        strcpy(r->errmsg, "missing parameter: PCGI_PID_FILE");
        return(-1);
    }

/* Add this at a later date:  jhb - 8/10/98 */
/*
    if (r->sockport && !r->sockhost[0])
    {
        strcpy(r->errmsg, "unable to determine hostname, recommend specifying: PCGI_HOST");
        return(-1);
    }
*/
    return(0);
}

int pcgiPutEnvironment(char *buf)
{
    /*
    // Stick a copy of the name=value pair in the
    // process environment. Note that this would
    // leak and need to be changed for any pcgi
    // implementations that work as web server api
    // extensions...
    */
    char *v = NULL;
    if((v=malloc(strlen(buf) + sizeof(char))) == NULL)
    {   
        return(-1);
    }
    strcpy(v, buf);
    if(putenv(v))
    {   
        return(-1);
    }
    return(0);
}

int pcgiPutNameValueInEnvironment(char *name, char *value)
{
    /* 
    //  Slight modification to pcgiPutEnvironment(), convenience function.
    */
    char *v = NULL;
    if ((v=malloc(strlen(name) + strlen(value) + (2 * sizeof(char)))) == NULL)
        return(-1);
    sprintf(v, "%s=%s", name, value);

    if(putenv(v))
        return(-1);
    return(0);
}

int pcgiTruthValue(char v)
{
    if (v=='1' || v=='t' || v=='T' || v=='y' || v=='Y') 
        return 1; 
    else if (v=='0' || v=='f' || v=='F' || v=='n' || v=='N') 
        return 0;
    else
        return -1;
}

#ifdef WIN32
/*
    This function lets both Unix & Win32 info files
    to use the same '/' character as a path separator.
    However it does this by assuming that we always
    want '\' backslashes as path separators in a
    Win32 environment.
*/
void amendPathSeparators(char *src)
{
    char ch, *ptr;
    ptr = src;
    while ((ch = *src++))
    {
        if (ch == PATHSEP_UNIX) { *ptr = PATHSEP_WIN32; }
        *ptr++;
    }
}
#endif

#ifdef MAIN_PARSEINFO
int main(int argc, char *argv[])
{
    /* char **env; */
    pcgiResource resource;
    pcgiResource *r = &resource;

    if (argc < 2)
    {
        printf("usage: parseinfo <pcgi-info-file>\n");
        return(-1);
    }

#ifdef CLOSE_FDS
    CloseFileDescriptors = 1;
#endif

    /* initialize pcgiResource */
    memset(r,0,sizeof(pcgiResource));
    r->conn=-1;

    strcpy(r->sw_info, argv[1]);
    if ((pcgiParseInfo(r)) < 0)
    {
        printf("error parsing info file: %s\n", r->sw_info);
        printf("  %s\n", r->errmsg);
        return(-1);
    }

    printf("pcgi resource attributes:\n");
    printf("  %-20s %s\n", "r->sw_info", r->sw_info);
    printf("  %-20s %s\n", "r->sw_name", r->sw_name);
    printf("  %-20s %s\n", "r->sw_home", r->sw_home);
    printf("  %-20s %s\n", "r->sw_exe", r->sw_exe);
    printf("  %-20s %s\n", "r->procpath", r->procpath);
    printf("  %-20s %s\n", "r->sockpath", r->sockpath);
    printf("  %-20s %s\n", "r->modpath", r->modpath);
    printf("  %-20s %s\n", "r->pubpath", r->pubpath);
    printf("  %-20s %d\n", "r->procid", r->procid);
    printf("  %-20s %s\n", "r->insertPath", r->insertPath);
    printf("  %-20s %s\n", "r->pythonPath", r->pythonPath);
    printf("  %-20s %d\n", "r->sockport", r->sockport);
    printf("  %-20s %s\n", "r->sockhost", r->sockhost);
    printf("  %-20s %d\n", "r->displayErrors", r->displayErrors);
    printf("  %-20s %d\n", "CloseFileDescriptors", CloseFileDescriptors);
    /* printf("\nenvironment:\n");         */
    /* for (env=environ; *env != 0; env++) */
    /*     printf("  %s\n", *env);         */
}
#endif
