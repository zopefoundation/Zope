##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################
__doc__="""Python Object Publisher -- Publish Python objects on web servers

$Id: Publish.py,v 1.123 1999/02/18 17:17:56 jim Exp $"""
__version__='$Revision: 1.123 $'[11:-2]

import sys, os
from string import lower, atoi, rfind, strip
from Response import Response
from Request import Request
from maybe_lock import allocate_lock

def publish(request, module_name, after_list, debug=0):

    request_get=request.get
    response=request.response

    # First check for "cancel" redirect:
    cancel=''
    if lower(strip(request_get('SUBMIT','')))=='cancel':
        cancel=request_get('CANCEL_ACTION','')
        if cancel: raise 'Redirect', cancel

    bobo_before, bobo_after, object, realm, debug_mode = get_module_info(
        module_name)

    after_list[0]=bobo_after
    if debug_mode: response.debug_mode=debug_mode
    if realm and not request.get('REMOTE_USER',None):
        response.realm=realm

    if bobo_before is not None: bobo_before();

    # Get a nice clean path list:
    path=strip(request_get('PATH_INFO'))

    request['PARENTS']=parents=[object]

    # Attempt to start a transaction:
    try: transaction=get_transaction()
    except: transaction=None
    if transaction is not None: transaction.begin()

    object=request.traverse(path)

    # Record transaction meta-data
    if transaction is not None:
        info="\t" + request_get('PATH_INFO')   
        auth_user=request_get('AUTHENTICATED_USER',None)
        if auth_user is not None:
            
            info=("%s %s" %
                  (request_get('AUTHENTICATION_PATH'), auth_user))+info
        transaction.note(info)

    # Now get object meta-data to decide if and how it should be called:
    object_as_function=object
            
    # First, assume we have a method:
    if hasattr(object_as_function,'im_func'):
        f=object_as_function.im_func
        c=f.func_code
        defaults=f.func_defaults
        argument_names=c.co_varnames[1:c.co_argcount]
    else:
        # Rather than sniff for FunctionType, assume its a
        # function and fall back to returning the object itself:        
        if hasattr(object_as_function,'func_defaults'):
            defaults=object_as_function.func_defaults
            c=object_as_function.func_code
            argument_names=c.co_varnames[:c.co_argcount]

            # Make sure we don't have a class that smells like a func
            if hasattr(object_as_function, '__bases__'):
                self.forbiddenError(entry_name)
            
        else: return response.setBody(object)

    args=[]
    nrequired=len(argument_names) - (len(defaults or []))
    for name_index in range(len(argument_names)):
        argument_name=argument_names[name_index]
        v=request_get(argument_name, args)
        if v is args:
            if argument_name=='self': args.append(parents[0])
            elif name_index < nrequired:
                self.badRequestError(argument_name)
            else: args.append(defaults[name_index-nrequired])
        else: args.append(v)

    args=tuple(args)
    if debug: result=call_object(object,args)
    else:     result=apply(object,args)

    if result and result is not response: response.setBody(result)

    if transaction: transaction.commit()

    return response

def call_object(object,args):
    result=apply(object,args) # Type s<cr> to step into published object.
    return result

_l=allocate_lock()
def get_module_info(module_name, modules={},
                    acquire=_l.acquire,
                    release=_l.release,
                    ):

    if modules.has_key(module_name): return modules[module_name]

    if module_name[-4:]=='.cgi': module_name=module_name[:-4]

    acquire()
    tb=None
    try:
      try:
        module=__import__(module_name, globals(), globals(), ('__doc__',))
    
        realm=module_name
                
        # Let the app specify a realm
        if hasattr(module,'__bobo_realm__'):
            realm=module.__bobo_realm__
        elif os.environ.has_key('Z_REALM'):
            realm=os.environ['Z_REALM']
        elif os.environ.has_key('BOBO_REALM'):
            realm=os.environ['BOBO_REALM']
        else: realm=module_name

        # Check for debug mode
        if hasattr(module,'__bobo_debug_mode__'):
            debug_mode=not not module.__bobo_debug_mode__
        elif (os.environ.has_key('Z_DEBUG_MODE') or
              os.environ.has_key('BOBO_DEBUG_MODE')):
            if os.environ.has_key('Z_DEBUG_MODE'):
                debug_mode=lower(os.environ['Z_DEBUG_MODE'])
            else:
                debug_mode=lower(os.environ['BOBO_DEBUG_MODE'])
            if debug_mode=='y' or debug_mode=='yes':
                debug_mode=1
            else:
                try: debug_mode=atoi(debug_mode)
                except: debug_mode=None
        else: debug_mode=None
 
        if hasattr(module,'__bobo_before__'):
            bobo_before=module.__bobo_before__
        else: bobo_before=None
                
        if hasattr(module,'__bobo_after__'): bobo_after=module.__bobo_after__
        else: bobo_after=None
    
        if hasattr(module,'bobo_application'):
            object=module.bobo_application
        elif hasattr(module,'web_objects'):
            object=module.web_objects
        else: object=module
    
        info= (bobo_before, bobo_after, object, realm, debug_mode)
    
        modules[module_name]=modules[module_name+'.cgi']=info

        return info
      except:
          t,v,tb=sys.exc_info()
          v=str(v)
          raise ImportError, (t, v), tb
    finally:
        tb=None
        release()

def publish_module(module_name,
                   stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                   environ=os.environ, debug=0):
    must_die=0
    status=200
    after_list=[None]
    request=None
    try:
        try:
            try:
                response=Response(stdout=stdout, stderr=stderr)
                request=Request(stdin, environ, response)
            finally:
                pass
            response = publish(request, module_name, after_list, debug=debug)
        except SystemExit, v:
            if hasattr(sys, 'exc_info'): must_die=sys.exc_info()
            else: must_die = SystemExit, v, sys.exc_traceback
            response.exception(must_die)
        except ImportError, v:
            if type(v) is type(()) and len(v)==3: must_die=v
            elif hasattr(sys, 'exc_info'): must_die=sys.exc_info()
            else: must_die = SystemExit, v, sys.exc_traceback
            response.exception(1, v)
        except:
            response.exception()
            status=response.getStatus()
        if response:
            response=str(response)
        if response: stdout.write(response)

        # The module defined a post-access function, call it
        if after_list[0] is not None: after_list[0]()

    finally:
        if request is not None: request.other={}

    if must_die: raise must_die[0], must_die[1], must_die[2]
    sys.exc_type, sys.exc_value, sys.exc_traceback = None, None, None
    return status

