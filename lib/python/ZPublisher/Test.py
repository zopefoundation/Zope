#!/usr/local/bin/python1.4
# $What$

__doc__='''Command-line Bobo

Usage

   bobo [options] module_path [path_info]

   where:

   module_path -- is a full path to a published module 

   path_info -- Is the information after the module name that would
         normally be specified in a GET URL, including a query string.

Description

   The command-line interface to Bobo provides a handy way to test,
   debug, and profile Bobo without a web server.  

Options

   -u username:password        -- Supply HTTP authorization information

   -e name=value               -- Supply environment variables.  Use a
                                  seperate -e option for each variable 
                                  specified.

   -p profiler_data_file       -- Run under profiler control,
                                  generating the profiler 
				  data file, profiler_data_file.

   -t                          -- Compute the time required to
                                  complete a request, in 
				  milliseconds.

   -r n                        -- Specify a repeat count for timing or
                                  profiling.

   -d                          -- Run in debug mode.  With this
				  option, bobo will run under Python
				  debugger control.  Two useful
				  breakpoints are set.  The first is
				  at the beginning of the module
				  publishing code.  Steping through
				  this code shows how bobo finds
				  objects and obtains certain
				  meta-data.  The second breakpoint is
				  at the point just before the
				  published object is called.  To jump
				  to the second breakpoint, you must
				  enter 's' followed by a carriage
				  return to step into the module, then
				  enter a 'c' followed by a carriage
				  return to jump to the first
				  breakpoint and then another 'c'
				  followed by a carriage return to
				  jump to the point where the object
				  is called.  Finally, enter 's'
				  followed a carriage return.

   -s                             Don't generate any output

Examples

   For example, to debug a published object (such as a method), spam,
   the following might be entered::

	    bobo -d /prj/lib/python/mymod container/spam
            s
            c
            c
            s


$Id: Test.py,v 1.11 1997/04/22 03:47:29 jim Exp $
'''
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
#  
#
# If you have questions regarding this software,
# contact:
#
#   Jim Fulton, jim@digicool.com
#
#   (540) 371-6909
#
#
# 
__version__='$Revision: 1.11 $'[11:-2]


#! /usr/local/bin/python

import sys,traceback, profile
repeat_count=100

def main():
    import sys, os, getopt, string
    global repeat_count

    try:
	optlist,args=getopt.getopt(sys.argv[1:], 'dtu:p:r:e:s')
	if len(args) > 2 or len(args) < 2: raise TypeError, None
	if len(args) == 2: path_info=args[1]
    except:
	sys.stderr.write(__doc__)
	sys.exit(-1)

    silent=profile=u=debug=timeit=None
    env={}
    for opt,val in optlist:
	if opt=='-d':
	    debug=1
	if opt=='-s':
	    silent=1
	if opt=='-t':
	    timeit=1
	if opt=='-u':
	    u=val
	elif opt=='-p':
	    profile=val
	elif opt=='-r':
	    repeat_count=string.atoi(val)
	elif opt=='-e':
	    opt=string.find(val,'=')
	    if opt <= 0: raise 'Invalid argument to -e', val
	    env[val[:opt]]=val[opt+1:]

    if (debug or 0)+(timeit or 0)+(profile and 1 or 0) > 1:
	raise 'Invalid options', 'only one of -p, -t, and -d are allowed' 

    module=args[0]

    publish(module,path_info,u=u,p=profile,d=debug,t=timeit,e=env,s=silent)



def time(function,*args,**kwargs):
    from timing import start, finish, milli

    repeat_range=range(repeat_count)
    apply(function,args,kwargs)
    start()
    for i in repeat_range:
	apply(function,args,kwargs)
    finish()

    return float(milli())/len(repeat_range)



def run(statement, *args):
    import sys, profile, time

    prof = profile.Profile(time.time)
    try:
	prof = prof.run(statement)
    except SystemExit:
	pass
    if args:
	prof.dump_stats(args[0])
    else:
	return prof.print_stats()


def publish(script,path_info,u=None,p=None,d=None,t=None,e={},s=None):

    import sys, os, getopt, string

    profile=p
    debug=d
    timeit=t
    silent=s

    if script[0]=='+': script='../../lib/python/'+script[1:]

    env=e
    env['SERVER_NAME']='bobo.server'
    env['SERVER_PORT']='80'
    env['REQUEST_METHOD']='GET'
    env['REMOTE_ADDR']='204.183.226.81 '
    env['REMOTE_HOST']='bobo.remote.host'
    env['HTTP_USER_AGENT']='Bobo/%s' % __version__
    env['HTTP_HOST']='ninny.digicool.com:8081 '
    env['SERVER_SOFTWARE']='Bobo/%s' % __version__
    env['SERVER_PROTOCOL']='HTTP/1.0 '
    env['HTTP_ACCEPT']='image/gif, image/x-xbitmap, image/jpeg, */* '
    env['SERVER_HOSTNAME']='bobo.server.host'
    env['GATEWAY_INTERFACE']='CGI/1.1 '
    env['SCRIPT_NAME']=script
    p=string.split(path_info,'?')
    if   len(p)==1: env['PATH_INFO'] = p[0]
    elif len(p)==2: [env['PATH_INFO'], env['QUERY_STRING']]=p
    else: raise TypeError, ''

    if u:
	import base64
	env['HTTP_AUTHORIZATION']="Basic %s" % base64.encodestring(u)

    dir,file=os.path.split(script)
    cdir=os.path.join(dir,'Components')
    sys.path[0:0]=[dir,cdir,os.path.join(cdir,sys.platform)]

    # We delay import to here, in case cgi_module_publisher is part of the
    # application distribution.
    from cgi_module_publisher import publish_module

    if profile:
	import __main__
	__main__.publish_module=publish_module
	__main__.file=file
	__main__.env=env
	print profile
	publish_module(file, environ=env, stdout=open('/dev/null','w'))
	c=("for i in range(%s): "
	   "publish_module(file, environ=env, stdout=open('/dev/null','w'))"
	   % repeat_count
	   )
	if profile: run(c,profile)
	else: run(c)
    elif debug:
	import cgi_module_publisher
	from cgi_module_publisher import ModulePublisher
	import pdb

	class Pdb(pdb.Pdb):
	    def do_pub(self,arg):
		if hasattr(self,'done_pub'):
		    print 'pub already done.'
		else:
		    self.do_s('')
		    self.do_s('')
		    self.do_c('')
		    self.done_pub=1
	    def do_ob(self,arg):
		if hasattr(self,'done_ob'):
		    print 'ob already done.'
		else:
		    self.do_pub('')
		    self.do_c('')
		    self.done_ob=1

	import codehack
       	db=Pdb()

	def fbreak(db,meth,codehack=codehack):
	    try: meth=meth.im_func
	    except AttributeError: pass
	    code=meth.func_code
	    lineno = codehack.getlineno(code)
	    filename = code.co_filename
	    db.set_break(filename,lineno)

	fbreak(db,ModulePublisher.publish)
	fbreak(db,ModulePublisher.call_object)
	fbreak(db,cgi_module_publisher.new_find_object)
	fbreak(db,cgi_module_publisher.old_find_object)

	dbdata={'breakpoints':(), 'env':env}
	b=''
	try: b=open('.bobodb','r').read()
	except: pass
	if b: exec b in dbdata

	for b in dbdata['breakpoints']:
	    if type(b) is type(()):
		apply(db.set_break,b)
	    else:
		fbreak(db,b)	

	db.prompt='pdb> '
	# db.set_continue()

	print (
	'* Type "s<cr>c<cr>" to jump to beginning of real publishing process.\n'
	'* Then type c<cr> to jump to the beginning of the URL traversal\n'
	'  algorithm.\n'
	'* Then type c<cr> to jump to published object call.'
	)
	db.run('publish_module(file,environ=env,debug=1)',
	       cgi_module_publisher.__dict__,
	       {'file':file, 'env':env})
    elif timeit:
	stdout=sys.stdout
	t= time(publish_module,file,
		stdout=open('/dev/null','w'), environ=env)
	stdout.write('%s milliseconds\n' % t)
    else:
	if silent: stdout=open('/dev/null','w')
	else: stdout=sys.stdout
	publish_module(file, environ=env, stdout=stdout)
	print '\n%s\n' % ('_'*60)

if __name__ == "__main__": main()

#
# $Log: Test.py,v $
# Revision 1.11  1997/04/22 03:47:29  jim
# *** empty log message ***
#
# Revision 1.10  1997/04/11 22:45:22  jim
# Changed to require two arguments.
#
# Revision 1.9  1997/04/11 13:35:06  jim
# Added -e option to specify environment variables.
#
# Revision 1.8  1997/04/10 13:48:56  jim
# Modified profiling to use repeat_count.
#
# Revision 1.7  1997/04/09 21:08:04  jim
# Improved profiling behavior:
#
#   - Do 10 trials, with a preceeding trial to warm things up,
#   - Use time.time for timing rather than os.times.
#
# Revision 1.6  1997/02/14 17:28:55  jim
# Added -r option to specify repeat count fot -t.
#
# Revision 1.5  1996/11/11 22:14:26  jim
# Minor doc change
#
# Revision 1.4  1996/11/11 22:00:01  jim
# Minor doc change
#
# Revision 1.3  1996/10/02 16:03:59  jim
# Took out spurious line.
#
# Revision 1.2  1996/09/16 14:43:26  jim
# Changes to make shutdown methods work properly.  Now shutdown methods
# can simply sys.exit(0).
#
# Added on-line documentation and debugging support to bobo.
#
# Revision 1.1  1996/09/13 22:51:52  jim
# *** empty log message ***
#
