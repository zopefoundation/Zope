##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
__doc__='''Generic Database adapter


$Id: DA.py,v 1.75 1999/11/16 20:19:52 jeffrey Exp $'''
__version__='$Revision: 1.75 $'[11:-2]

import OFS.SimpleItem, Aqueduct, RDB
import DocumentTemplate, marshal, md5, base64, Acquisition, os
from Aqueduct import decodestring, parse
from Aqueduct import custom_default_report, default_input_form
from Globals import HTMLFile, MessageDialog
from cStringIO import StringIO
import sys, Globals, OFS.SimpleItem, AccessControl.Role
from string import atoi, find, join, split
import DocumentTemplate, sqlvar, sqltest, sqlgroup
from time import time
from zlib import compress, decompress
from DateTime.DateTime import DateTime
md5new=md5.new
import ExtensionClass
import DocumentTemplate.DT_Util
from cPickle import dumps, loads
from Results import Results
from App.Extensions import getBrain


try: from IOBTree import Bucket
except: Bucket=lambda:{}


class SQL(DocumentTemplate.HTML):
    commands={}
    for k, v in DocumentTemplate.HTML.commands.items(): commands[k]=v
    commands['sqlvar' ]=sqlvar.SQLVar
    commands['sqltest']=sqltest.SQLTest
    commands['sqlgroup' ]=sqlgroup.SQLGroup


class DA(
    Aqueduct.BaseQuery,Acquisition.Implicit,
    Globals.Persistent,
    AccessControl.Role.RoleManager,
    OFS.SimpleItem.Item,
    ):
    'Database Adapter'

    _col=None
    max_rows_=1000
    cache_time_=0
    max_cache_=100
    class_name_=class_file_=''
    allow_simple_one_argument_traversal=None
    
    manage_options=(
        {'label':'Edit', 'action':'manage_main'},
        {'label':'Test', 'action':'manage_testForm'},
        {'label':'Advanced', 'action':'manage_advancedForm'},
        {'label':'Security', 'action':'manage_access'},
        )
 
    # Specify how individual operations add up to "permissions":
    __ac_permissions__=(
        ('View management screens',
         (
        'manage_main', 'index_html',
        'manage_advancedForm', 'PrincipiaSearchSource'
        )),
        ('Change Database Methods',
         ('manage_edit','manage_advanced', 'manage_testForm','manage_test')),
        ('Use Database Methods', ('__call__',''), ('Anonymous','Manager')),
        )
   

    def __init__(self, id, title, connection_id, arguments, template):
        self.id=id
        self.manage_edit(title, connection_id, arguments, template)
    
    manage_advancedForm=HTMLFile('advanced', globals())

    test_url___roles__=None
    def test_url_(self):
        'Method for testing server connection information'
        return 'PING'

    _size_changes={
        'Bigger': (5,5),
        'Smaller': (-5,-5),
        'Narrower': (0,-5),
        'Wider': (0,5),
        'Taller': (5,0),
        'Shorter': (-5,0),
        }

    def _er(self,title,connection_id,arguments,template,
            SUBMIT,sql_pref__cols,sql_pref__rows,REQUEST):
        dr,dc = self._size_changes[SUBMIT]
        
        rows=max(1,atoi(sql_pref__rows)+dr)
        cols=max(40,atoi(sql_pref__cols)+dc)
        e=(DateTime('GMT') + 365).rfc822()
        resp=REQUEST['RESPONSE']
        resp.setCookie('sql_pref__rows',str(rows),path='/',expires=e)
        resp.setCookie('sql_pref__cols',str(cols),path='/',expires=e)
        return self.manage_main(
            self,REQUEST,
            title=title,
            arguments_src=arguments,
            connection_id=connection_id,
            src=template,
            sql_pref__cols=cols,sql_pref__rows=rows)

    def manage_edit(self,title,connection_id,arguments,template,
                    SUBMIT='Change',sql_pref__cols='50', sql_pref__rows='20',
                    REQUEST=None):
        """Change database method  properties

        The 'connection_id' argument is the id of a database connection
        that resides in the current folder or in a folder above the
        current folder.  The database should understand SQL.

        The 'arguments' argument is a string containing an arguments
        specification, as would be given in the SQL method cration form.

        The 'template' argument is a string containing the source for the
        SQL Template.
        """

        if self._size_changes.has_key(SUBMIT):
            return self._er(title,connection_id,arguments,template,
                            SUBMIT,sql_pref__cols,sql_pref__rows,REQUEST)

        self.title=title
        self.connection_id=connection_id
        self.arguments_src=arguments
        self._arg=parse(arguments)
        self.src=template
        self.template=t=SQL(template)
        t.cook()
        self._v_cache={}, Bucket()
        if REQUEST:
            if SUBMIT=='Change and Test':
                return self.manage_testForm(REQUEST)
            message='ZSQL Method content changed'
            return self.manage_main(self, REQUEST, manage_tabs_message=message)
        return ''


    def manage_advanced(self, max_rows, max_cache, cache_time,
                        class_name, class_file, direct=None,
                        REQUEST=None):
        """Change advanced properties

        The arguments are:

        max_rows -- The maximum number of rows to be returned from a query.

        max_cache -- The maximum number of results to cache

        cache_time -- The maximum amound of time to use a cached result.

        class_name -- The name of a class that provides additional
          attributes for result record objects. This class will be a
          base class of the result record class.

        class_file -- The name of the file containing the class
          definition.

        The class file normally resides in the 'Extensions'
        directory, however, the file name may have a prefix of
        'product.', indicating that it should be found in a product
        directory.

        For example, if the class file is: 'ACMEWidgets.foo', then an
        attempt will first be made to use the file
        'lib/python/Products/ACMEWidgets/Extensions/foo.py'. If this
        failes, then the file 'Extensions/ACMEWidgets.foo.py' will be
        used.
  
        """
        self.max_rows_ = max_rows
        self.max_cache_, self.cache_time_ = max_cache, cache_time
        self._v_cache={}, Bucket()
        self.class_name_, self.class_file_ = class_name, class_file
        self._v_brain=getBrain(self.class_file_, self.class_name_, 1)
        self.allow_simple_one_argument_traversal=direct
        if REQUEST is not None:
            m="ZSQL Method advanced settings have been set"
            return self.manage_advancedForm(self,REQUEST,manage_tabs_message=m)
##            return self.manage_editedDialog(REQUEST)

    #def getFindContent(self):
    #    """Return content for use by the Find machinery."""
    #    return '%s\n%s' % (self.arguments_src, self.src)

    def PrincipiaSearchSource(self):
        """Return content for use by the Find machinery."""
        return '%s\n%s' % (self.arguments_src, self.src)
    
    def manage_testForm(self, REQUEST):
        " "
        input_src=default_input_form(self.title_or_id(),
                                     self._arg, 'manage_test',
                                     '<dtml-var manage_tabs>')
        return DocumentTemplate.HTML(input_src)(self, REQUEST, HTTP_REFERER='')

    def manage_test(self, REQUEST):
        ' '

        src="Could not render the query template!"
        result=()
        t=v=tb=None
        try:
            try:
                src=self(REQUEST, src__=1)
                if find(src,'\0'): src=join(split(src,'\0'),'\n'+'-'*60+'\n')
                result=self(REQUEST, test__=1)
                if result._searchable_result_columns():
                    r=custom_default_report(self.id, result)
                else:
                    r='This was not a query.'
            except:
                t, v, tb = sys.exc_info()
                r='<strong>Error, <em>%s</em>:</strong> %s' % (t, v)

            report=DocumentTemplate.HTML(
                '<html><BODY BGCOLOR="#FFFFFF" LINK="#000099" VLINK="#555555">\n'
                '<dtml-var manage_tabs>\n<hr>\n%s\n\n'
                '<hr><strong>SQL used:</strong><br>\n<pre>\n%s\n</pre>\n<hr>\n'
                '</body></html>'
                % (r,src))

            report=apply(report,(self,REQUEST),{self.id:result})

            if tb is not None:
                self.raise_standardErrorMessage(
                    None, REQUEST, t, v, tb, None, report)

            return report
        
        finally: tb=None

    def index_html(self, URL1):
        " "
        raise 'Redirect', ("%s/manage_testForm" % URL1)

    def _searchable_arguments(self): return self._arg

    def _searchable_result_columns(self): return self._col

    def _cached_result(self, DB__, query):

        # Try to fetch from cache
        if hasattr(self,'_v_cache'): cache=self._v_cache
        else: cache=self._v_cache={}, Bucket()
        cache, tcache = cache
        max_cache=self.max_cache_
        now=time()
        t=now-self.cache_time_
        if len(cache) > max_cache / 2:
            keys=tcache.keys()
            keys.reverse()
            while keys and (len(keys) > max_cache or keys[-1] < t):
                key=keys[-1]
                q=tcache[key]
                del tcache[key]
                del cache[q]
                del keys[-1]
                
        if cache.has_key(query):
            k, r = cache[query]
            if k > t: return r

        result=apply(DB__.query, query)
        if self.cache_time_ > 0:
            tcache[int(now)]=query
            cache[query]= now, result

        return result

    def __call__(self, REQUEST=None, __ick__=None, src__=0, test__=0, **kw):
        """Call the database method

        The arguments to the method should be passed via keyword
        arguments, or in a single mapping object. If no arguments are
        given, and if the method was invoked through the Web, then the
        method will try to acquire and use the Web REQUEST object as
        the argument mapping.

        The returned value is a sequence of record objects.
        """

        if REQUEST is None:
            if kw: REQUEST=kw
            else:
                if hasattr(self, 'REQUEST'): REQUEST=self.REQUEST
                else: REQUEST={}

        try: dbc=getattr(self, self.connection_id)
        except AttributeError:
            raise AttributeError, (
                "The database connection <em>%s</em> cannot be found." % (
                self.connection_id))

        try: DB__=dbc()
        except: raise 'Database Error', (
            '%s is not connected to a database' % self.id)
        
        if hasattr(self, 'aq_parent'):
            p=self.aq_parent
        else: p=None

        argdata=self._argdata(REQUEST)
        argdata['sql_delimiter']='\0'
        argdata['sql_quote__']=dbc.sql_quote__
        query=apply(self.template, (p,), argdata)

        if src__: return query

        if self.cache_time_ > 0 and self.max_cache_ > 0:
            result=self._cached_result(DB__, (query, self.max_rows_))
        else: result=DB__.query(query, self.max_rows_)

        if hasattr(self, '_v_brain'): brain=self._v_brain
        else:
            brain=self._v_brain=getBrain(self.class_file_, self.class_name_)

        if type(result) is type(''):
            f=StringIO()
            f.write(result)
            f.seek(0)
            result=RDB.File(f,brain,p)
        else:
            result=Results(result, brain, p)
        columns=result._searchable_result_columns()
        if test__ and columns != self._col: self._col=columns
        return result

    def da_has_single_argument(self): return len(self._arg)==1

    def __getitem__(self, key):
        args=self._arg
        if self.allow_simple_one_argument_traversal and len(args)==1:
            results=self({args.keys()[0]: key})
            if results:
                if len(results) > 1: raise KeyError, key
            else: raise KeyError, key
            r=results[0]
            # if hasattr(self, 'aq_parent'): r=r.__of__(self.aq_parent)
            return r
            
        self._arg[key] # raise KeyError if not an arg
        return Traverse(self,{},key)

    def connectionIsValid(self):
        return (hasattr(self, self.connection_id) and
                hasattr(getattr(self, self.connection_id), 'connected'))

    def connected(self):
        return getattr(getattr(self, self.connection_id), 'connected')()

Globals.default__class_init__(DA)



ListType=type([])
class Traverse(ExtensionClass.Base):
    """Helper class for 'traversing' searches during URL traversal
    """
    _r=None
    _da=None

    def __init__(self, da, args, name=None):
        self._da=da
        self._args=args
        self._name=name

    def __bobo_traverse__(self, REQUEST, key):
        name=self._name
        da=self.__dict__['_da']
        args=self._args
        if name:
            if args.has_key(name):
                v=args[name]
                if type(v) is not ListType: v=[v]
                v.append(key)
                key=v

            args[name]=key

            if len(args) < len(da._arg):            
                return self.__class__(da, args)
            key=self # "consume" key

        elif da._arg.has_key(key): return self.__class__(da, args, key)

        results=da(args)
        if results:
            if len(results) > 1:
                try: return results[atoi(key)].__of__(da)
                except: raise KeyError, key
        else: raise KeyError, key
        r=results[0]
        # if hasattr(da, 'aq_parent'): r=r.__of__(da.aq_parent)
        self._r=r

        if key is self: return r

        if hasattr(r,'__bobo_traverse__'):
            try: return r.__bobo_traverse__(REQUEST, key)
            except: pass

        try: return getattr(r,key)
        except AttributeError, v:
            if str(v) != key: raise AttributeError, v

        return r[key]

    def __getattr__(self, name):
        r=self.__dict__['_r']
        if hasattr(r, name): return getattr(r,name)
        return getattr(self.__dict__['_da'], name)

