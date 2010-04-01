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
__doc__='''Generic Database adapter'''
__version__='$Revision: 1.116 $'[11:-2]

from cStringIO import StringIO
import re
import string
import sys
from time import time

from AccessControl.DTML import RestrictedDTML
from AccessControl.Permissions import change_database_methods
from AccessControl.Permissions import use_database_methods
from AccessControl.Permissions import view_management_screens
from AccessControl.Role import RoleManager
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import Implicit
from App.class_init import InitializeClass
from App.Extensions import getBrain
from App.special_dtml import DTMLFile
from DocumentTemplate import HTML
from DocumentTemplate.html_quote import html_quote
from DateTime.DateTime import DateTime
from ExtensionClass import Base
from BTrees.OOBTree import OOBucket as Bucket
from OFS.SimpleItem import Item
from Persistence import Persistent
from webdav.Resource import Resource
from webdav.Lockable import ResourceLockedError
from zExceptions import BadRequest

from Aqueduct import BaseQuery
from Aqueduct import custom_default_report
from Aqueduct import default_input_form
from Aqueduct import parse
from RDB import File
from Results import Results
from sqlgroup import SQLGroup
from sqltest import SQLTest
from sqlvar import SQLVar


class DatabaseError(BadRequest):
   " base class for external relational data base connection problems "
   pass


class nvSQL(HTML):
    # Non-validating SQL Template for use by SQLFiles.
    commands={}
    for k, v in HTML.commands.items():
        commands[k]=v
    commands['sqlvar'] = SQLVar
    commands['sqltest'] = SQLTest
    commands['sqlgroup' ] = SQLGroup

    _proxy_roles=()


class SQL(RestrictedDTML, Base, nvSQL):
    # Validating SQL template for Zope SQL Methods.
    pass


class DA(BaseQuery,
         Implicit,
         Persistent,
         RoleManager,
         Item,
         Resource
        ):
    'Database Adapter'

    security = ClassSecurityInfo()
    security.declareObjectProtected(use_database_methods)
    security.setPermissionDefault(use_database_methods,
                                  ('Anonymous', 'Manager'))

    _col=None
    max_rows_=1000
    cache_time_=0
    max_cache_=100
    class_name_=class_file_=''
    allow_simple_one_argument_traversal=None
    template_class=SQL
    connection_hook=None

    manage_options=(
        (
        {'label':'Edit', 'action':'manage_main',
         'help':('ZSQLMethods','Z-SQL-Method_Edit.stx')},
        {'label':'Test', 'action':'manage_testForm',
         'help':('ZSQLMethods','Z-SQL-Method_Test.stx')},
        {'label':'Advanced', 'action':'manage_advancedForm',
         'help':('ZSQLMethods','Z-SQL-Method_Advanced.stx')},
        )
        + RoleManager.manage_options
        + Item.manage_options
        )

    def __init__(self, id, title, connection_id, arguments, template):
        self.id=str(id)
        self.manage_edit(title, connection_id, arguments, template)

    security.declareProtected(view_management_screens, 'manage_advancedForm')
    manage_advancedForm=DTMLFile('dtml/advanced', globals())

    security.declarePublic('test_url')
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
            SUBMIT,dtpref_cols,dtpref_rows,REQUEST):
        dr,dc = self._size_changes[SUBMIT]
        rows = str(max(1, int(dtpref_rows) + dr))
        cols = str(dtpref_cols)
        if cols.endswith('%'):
           cols = str(min(100, max(25, int(cols[:-1]) + dc))) + '%'
        else:
           cols = str(max(35, int(cols) + dc))
        e = (DateTime("GMT") + 365).rfc822()
        setCookie = REQUEST["RESPONSE"].setCookie
        setCookie("dtpref_rows", rows, path='/', expires=e)
        setCookie("dtpref_cols", cols, path='/', expires=e)
        REQUEST.other.update({"dtpref_cols":cols, "dtpref_rows":rows})
        return self.manage_main(self, REQUEST, title=title,
                                arguments_src=arguments,
                                connection_id=connection_id, src=template)

    security.declareProtected(change_database_methods, 'manage_edit')
    def manage_edit(self,title,connection_id,arguments,template,
                    SUBMIT='Change', dtpref_cols='100%', dtpref_rows='20',
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
                            SUBMIT,dtpref_cols,dtpref_rows,REQUEST)

        if self.wl_isLocked():
            raise ResourceLockedError, 'SQL Method is locked via WebDAV'

        self.title=str(title)
        self.connection_id=str(connection_id)
        arguments=str(arguments)
        self.arguments_src=arguments
        self._arg=parse(arguments)
        template=str(template)
        self.src=template
        self.template=t=self.template_class(template)
        t.cook()
        self._v_cache={}, Bucket()
        if REQUEST:
            if SUBMIT=='Change and Test':
                return self.manage_testForm(REQUEST)
            message='ZSQL Method content changed'
            return self.manage_main(self, REQUEST, manage_tabs_message=message)
        return ''


    security.declareProtected(change_database_methods, 'manage_advanced')
    def manage_advanced(self, max_rows, max_cache, cache_time,
                        class_name, class_file, direct=None,
                        REQUEST=None, connection_hook=None):
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
        # paranoid type checking
        if type(max_rows) is not type(1):
            max_rows=string.atoi(max_rows)
        if type(max_cache) is not type(1):
            max_cache=string.atoi(max_cache)
        if type(cache_time) is not type(1):
            cache_time=string.atoi(cache_time)
        class_name=str(class_name)
        class_file=str(class_file)

        self.max_rows_ = max_rows
        self.max_cache_, self.cache_time_ = max_cache, cache_time
        self._v_cache={}, Bucket()
        self.class_name_, self.class_file_ = class_name, class_file
        self._v_brain=getBrain(self.class_file_, self.class_name_, 1)
        self.allow_simple_one_argument_traversal=direct

        self.connection_hook = connection_hook

        if REQUEST is not None:
            m="ZSQL Method advanced settings have been set"
            return self.manage_advancedForm(self,REQUEST,manage_tabs_message=m)

    security.declareProtected(view_management_screens, 'PrincipiaSearchSource')
    def PrincipiaSearchSource(self):
        """Return content for use by the Find machinery."""
        return '%s\n%s' % (self.arguments_src, self.src)


    # WebDAV / FTP support

    default_content_type = 'text/plain'

    security.declareProtected(view_management_screens, 'document_src')
    def document_src(self, REQUEST=None, RESPONSE=None):
        """Return unprocessed document source."""
        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', 'text/plain')
        return '<params>%s</params>\n%s' % (self.arguments_src, self.src)

    def manage_FTPget(self):
        """Get source for FTP download"""
        self.REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
        return '<params>%s</params>\n%s' % (self.arguments_src, self.src)

    def get_size(self): return len(self.document_src())

    security.declareProtected(change_database_methods, 'PUT')
    def PUT(self, REQUEST, RESPONSE):
        """Handle put requests"""
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        body = REQUEST.get('BODY', '')
        m = re.match('\s*<params>(.*)</params>\s*\n', body, re.I | re.S)
        if m:
            self.arguments_src = m.group(1)
            self._arg=parse(self.arguments_src)
            body = body[m.end():]
        template = body
        self.src = template
        self.template=t=self.template_class(template)
        t.cook()
        self._v_cache={}, Bucket()
        RESPONSE.setStatus(204)
        return RESPONSE


    security.declareProtected(change_database_methods, 'manage_testForm')
    def manage_testForm(self, REQUEST):
        " "
        input_src=default_input_form(self.title_or_id(),
                                     self._arg, 'manage_test',
                                     '<dtml-var manage_tabs>')
        return HTML(input_src)(self, REQUEST, HTTP_REFERER='')

    security.declareProtected(change_database_methods, 'manage_test')
    def manage_test(self, REQUEST):
        """Test an SQL method."""
        # Try to render the query template first so that the rendered
        # source will be available for the error message in case some
        # error occurs...
        try:    src=self(REQUEST, src__=1)
        except: src="Could not render the query template!"
        result=()
        t=v=tb=None
        try:
            try:
                src, result=self(REQUEST, test__=1)
                if string.find(src,'\0'):
                    src=string.join(string.split(src,'\0'),'\n'+'-'*60+'\n')
                if result._searchable_result_columns():
                    r=custom_default_report(self.id, result)
                else:
                    r='This statement returned no results.'
            except:
                t, v, tb = sys.exc_info()
                r='<strong>Error, <em>%s</em>:</strong> %s' % (t, v)

            report = HTML(
                '<html>\n'
                '<BODY BGCOLOR="#FFFFFF" LINK="#000099" VLINK="#555555">\n'
                '<dtml-var manage_tabs>\n<hr>\n%s\n\n'
                '<hr><strong>SQL used:</strong><br>\n<pre>\n%s\n</pre>\n<hr>\n'
                '</body></html>'
                % (r,html_quote(src)))

            report=apply(report,(self,REQUEST),{self.id:result})

            if tb is not None:
                self.raise_standardErrorMessage(
                    None, REQUEST, t, v, tb, None, report)

            return report

        finally: tb=None

    security.declareProtected(view_management_screens, 'index_html')
    def index_html(self, REQUEST):
        """ """
        REQUEST.RESPONSE.redirect("%s/manage_testForm" % REQUEST['URL1'])

    def _searchable_arguments(self): return self._arg

    def _searchable_result_columns(self): return self._col

    def _cached_result(self, DB__, query, max_rows, conn_id):
        # Try to fetch a result from the cache.
        # Compute and cache the result otherwise.
        # Also maintains the cache and ensures stale entries
        # are never returned and that the cache never gets too large.

        # NB: Correct cache behavior is predicated on Bucket.keys()
        #     returning a sequence ordered from smalled number
        #     (ie: the oldest cache entry) to largest number
        #     (ie: the newest cache entry). Please be careful if you
        #     change the class instantied below!

        # get hold of a cache
        caches = getattr(self,'_v_cache',None)
        if caches is None:
            caches = self._v_cache = {}, Bucket()
        cache, tcache = caches

        # the key for caching
        cache_key = query,max_rows,conn_id
        # the maximum number of result sets to cache
        max_cache=self.max_cache_
        # the current time
        now=time()
        # the oldest time which is not stale
        t=now-self.cache_time_
        
        # if the cache is too big, we purge entries from it
        if len(cache) >= max_cache:
            keys=tcache.keys()
            # We also hoover out any stale entries, as we're
            # already doing cache minimisation.
            # 'keys' is ordered, so we purge the oldest results
            # until the cache is small enough and there are no
            # stale entries in it
            while keys and (len(keys) >= max_cache or keys[0] < t):
                key=keys[0]
                q=tcache[key]
                del tcache[key]
                del cache[q]
                del keys[0]

        # okay, now see if we have a cached result
        if cache.has_key(cache_key):
            k, r = cache[cache_key]
            # the result may still be stale, as we only hoover out
            # stale results above if the cache gets too large.
            if k > t:
                # yay! a cached result returned!
                return r
            else:
                # delete stale cache entries
                del cache[cache_key]
                del tcache[k]

        # call the pure query
        result=DB__.query(query,max_rows)

        # When a ZSQL method is handled by one ZPublisher thread twice in
        # less time than it takes for time.time() to return a different
        # value, the SQL generated is different, then this code will leak
        # an entry in 'cache' for each time the ZSQL method generates
        # different SQL until time.time() returns a different value.
        #
        # On Linux, you would need an extremely fast machine under extremely
        # high load, making this extremely unlikely. On Windows, this is a
        # little more likely, but still unlikely to be a problem.
        #
        # If it does become a problem, the values of the tcache mapping
        # need to be turned into sets of cache keys rather than a single
        # cache key.
        tcache[now]=cache_key
        cache[cache_key]= now, result

        return result

    security.declareProtected(use_database_methods, '__call__')
    def __call__(self, REQUEST=None, __ick__=None, src__=0, test__=0, **kw):
        """Call the database method

        The arguments to the method should be passed via keyword
        arguments, or in a single mapping object. If no arguments are
        given, and if the method was invoked through the Web, then the
        method will try to acquire and use the Web REQUEST object as
        the argument mapping.

        The returned value is a sequence of record objects.
        """

        __traceback_supplement__ = (SQLMethodTracebackSupplement, self)

        if REQUEST is None:
            if kw:
                REQUEST=kw
            else:
                if hasattr(self, 'REQUEST'):
                    REQUEST=self.REQUEST
                else:
                    REQUEST={}

        # connection hook
        c = self.connection_id
        # for backwards compatability
        hk = self.connection_hook
        # go get the connection hook and call it
        if hk:
            c = getattr(self, hk)()
           
        try:
            dbc=getattr(self, c)
        except AttributeError:
            raise AttributeError, (
                "The database connection <em>%s</em> cannot be found." % (
                c))

        try:
            DB__=dbc()
        except: raise DatabaseError, (
            '%s is not connected to a database' % self.id)

        if hasattr(self, 'aq_parent'):
            p=self.aq_parent
        else:
            p=None

        argdata=self._argdata(REQUEST)
        argdata['sql_delimiter']='\0'
        argdata['sql_quote__']=dbc.sql_quote__

        security=getSecurityManager()
        security.addContext(self)
        try:
            try:
                query=apply(self.template, (p,), argdata)
            except TypeError, msg:
                msg = str(msg)
                if string.find(msg,'client') >= 0:
                    raise NameError("'client' may not be used as an " +
                        "argument name in this context")
                else: raise
        finally:
            security.removeContext(self)

        if src__:
            return query

        if self.cache_time_ > 0 and self.max_cache_ > 0:
            result=self._cached_result(DB__, query, self.max_rows_, c)
        else:
            result=DB__.query(query, self.max_rows_)

        if hasattr(self, '_v_brain'):
            brain=self._v_brain
        else:
            brain=self._v_brain=getBrain(self.class_file_, self.class_name_)

        if type(result) is type(''):
            f=StringIO()
            f.write(result)
            f.seek(0)
            result = File(f,brain,p, None)
        else:
            result = Results(result, brain, p, None)
        columns = result._searchable_result_columns()
        if test__ and columns != self._col:
            self._col=columns

        # If run in test mode, return both the query and results so
        # that the template doesn't have to be rendered twice!
        if test__:
            return query, result

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

InitializeClass(DA)


ListType=type([])
class Traverse(Base):
    """Helper class for 'traversing' searches during URL traversal
    """
    _da=None

    def __init__(self, da, args, name=None):
        self._r=None
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
                try: return results[string.atoi(key)].__of__(da)
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


class SQLMethodTracebackSupplement:
    def __init__(self, sql):
        self.object = sql
