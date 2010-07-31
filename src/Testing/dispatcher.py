##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

# Dispatcher for usage inside Zope test environment
# Andreas Jung, andreas@digicool.com 03/24/2001


import os,sys,re,string
import threading,time,commands,profile


class Dispatcher:

    """
    a multi-purpose thread dispatcher
    """

    def __init__(self,func=''):
        self.fp = sys.stderr
        self.f_startup = []
        self.f_teardown = []
        self.lastlog = ""
        self.lock = threading.Lock()
        self.func = func
        self.profiling = 0

        self.doc = getattr(self,self.func).__doc__

    def setlog(self,fp):
        self.fp = fp

    def log(self,s):
        if s==self.lastlog: return
        self.fp.write(s)
        self.fp.flush()
        self.lastlog=s

    def logn(self,s):
        if s==self.lastlog: return
        self.fp.write(s + '\n')
        self.fp.flush()
        self.lastlog=s


    def profiling_on():
        self.profiling = 1

    def profiling_off():
        self.profiling = 0


    def  dispatcher(self,name='', *params):
        """ dispatcher for threads
        The dispatcher expects one or several tupels:
        (functionname, number of threads to start , args, keyword args)
        """

        self.mem_usage  = [-1]

        mem_watcher = threading.Thread(None,self.mem_watcher,name='memwatcher')
        mem_watcher.start()

        self.start_test = time.time()
        self.name       = name
        self.th_data    = {}
        self.runtime    = {}
        self._threads   = []
        s2s=self.s2s


        for func,numthreads,args,kw in params:
            f = getattr(self,func)

            for i in range(0,numthreads):
                kw['t_func'] = func
                th = threading.Thread(None,self.worker,name="TH_%s_%03d" % (func,i) ,args=args,kwargs=kw)
                self._threads.append(th)

        for th in self._threads:           th.start()
        while threading.activeCount() > 1: time.sleep(1)

        self.logn('ID: %s ' % self.name)
        self.logn('FUNC: %s ' % self.func)
        self.logn('DOC: %s ' % self.doc)
        self.logn('Args: %s' % params)

        for th in self._threads:
            self.logn( '%-30s ........................ %9.3f sec' % (th.getName(), self.runtime[th.getName()]) )
            for k,v in self.th_data[th.getName()].items():
                self.logn ('%-30s  %-15s = %s' % (' ',k,v) )


        self.logn("")
        self.logn('Complete running time:                                  %9.3f sec' % (time.time()-self.start_test) )
        if len(self.mem_usage)>1: self.mem_usage.remove(-1)
        self.logn( "Memory: start: %s, end: %s, low: %s, high: %s" %  \
                        (s2s(self.mem_usage[0]),s2s(self.mem_usage[-1]),s2s(min(self.mem_usage)), s2s(max(self.mem_usage))))
        self.logn('')


    def worker(self,*args,**kw):

        for func in self.f_startup: f = getattr(self,func)()

        t_func = getattr(self,kw['t_func'])
        del kw['t_func']

        ts = time.time()
        apply(t_func,args,kw)
        te = time.time()

        for func in self.f_teardown: getattr(self,func)()



    def th_setup(self):
        """ initalize thread with some environment data """

        env = {'start': time.time()
                  }
        return env


    def th_teardown(self,env,**kw):
        """ famous last actions of thread """

        self.lock.acquire()
        self.th_data[ threading.currentThread().getName() ]   = kw
        self.runtime  [ threading.currentThread().getName() ] = time.time() - env['start']
        self.lock.release()


    def getmem(self):
        """ try to determine the current memory usage """

        if not sys.platform in ['linux2']: return None
        cmd = '/bin/ps --no-headers -o pid,vsize --pid %s' % os.getpid()
        outp = commands.getoutput(cmd)
        pid,vsize = filter(lambda x: x!="" , string.split(outp," ") )

        data = open("/proc/%d/statm" % os.getpid()).read()
        fields = re.split(" ",data)
        mem = string.atoi(fields[0]) * 4096


        return mem


    def mem_watcher(self):
        """ thread for watching memory usage """

        running = 1

        while running ==1:
            self.mem_usage.append( self.getmem() )
            time.sleep(1)
            if threading.activeCount() == 2: running = 0


    def register_startup(self,func):
        self.f_startup.append(func)

    def register_teardown(self,func):
        self.f_teardown.append(func)


    def s2s(self,n):
        import math
        if n <1024.0: return "%8.3lf Bytes" % n
        if n <1024.0*1024.0: return "%8.3lf KB" % (1.0*n/1024.0)
        if n <1024.0*1024.0*1024.0: return "%8.3lf MB" % (1.0*n/1024.0/1024.0)
        else: return n

if __name__=="__main__":

    d=Dispatcher()
    print d.getmem()
    pass
