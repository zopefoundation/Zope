"""gadfly server mode

   script usage 
   
    python gfserve.py port database directory password [startup]

   test example

    python gfserve.py 2222 test dbtest admin gfstest

   port is the port to listen to
   database is the database to start up. (must exist!)
   directory is the directory the database is in.
   password is the administrative access password.

   startup if present should be the name of a module to use
   for startup.  The Startup module must contain a function
   
    Dict = startup(admin_policy, connection, Server_instance)
       
   which performs any startup actions on the database needed
   and returns either None or a Dictionary of
   
       name --> policy objects
       
   where the policy objects describe policies beyond the
   admin policy.  The startup function may also
   modify the admin_policy (disabling queries for example).

   The arguments passed to startup are:
       admin_policy: the administrative policy
          eg you could turn queries off for admin, using admin
          only for server maintenance, or you could add prepared
          queries to the admin_policy.
       connection: the database connection
          eg you could perform some inserts before server start
          also needed to make policies.
       Server_instance
          Included for additional customization.

   Create policies using
       P = gfserve.Policy(name, password, connection, queries=0)
         -- for a "secure" policy with only prepared queries allowed,
   or
       P = gfserve.Policy(name, password, connection, queries=1)
         -- for a policy with full access arbitrary statement
            execution.

   add a "named prepared statement" to a policy using
       P[name] = statement
   for example
       P["updatenorm"] = '''
          update frequents
          set bar=?, perweek=?
          where drinker='norm'
        '''
   in this case 'updatenorm' requires 2 dynamic parameters when
   invoked from a client.
       
   Script stdout lists server logging information.

   Some server administration services (eg shutdown)
   are implemented by the script interpretion of gfclient.py.
"""

import socket, gadfly

from gfsocket import \
   reply_exception, reply_success, Packet_Reader, certify

def main():
    """start up the server."""
    import sys
    try:
        done = 0
        argv = sys.argv
        nargs = len(argv)
        #print nargs, argv
        if nargs<5:
            sys.stderr.write("gfserve: not enough arguments: %s\n\n" % argv)
            sys.stderr.write(__doc__)
            return
        [port, db, dr, pw] = argv[1:5]
        print "gfserve startup port=%s db=%s, dr=%s password omitted" % (
           port, db, dr)
        from string import atoi
        port = atoi(port)
        startup = None
        if nargs>5:
            startup = argv[5]
            print "gfserve: load startup module %s" % startup
        S = Server(port, db, dr, pw, startup)
        S.init()
        print "gfserve: server initialized, setting stderr=stdout"
        sys.stderr = sys.stdout
        print "gfserve: starting the server"
        S.start()
        done = 1
    finally:
        if not done:
            print __doc__

# general error
ServerError = "ServerError"

# no such prepared name
PreparedNameError = "PreparedNameError"

# actions

# shut down the server (admin policy only)
#   arguments = ()
#   shutdown the server with no checkpoint
SHUTDOWN = "SHUTDOWN"

# restart the server (admin only)
#   arguments = ()
#   restart the server (recover)
#   no checkpoint
RESTART = "RESTART"

# checkpoint the server (admin only)
#   arguments = ()
#   checkpoint the server
CHECKPOINT = "CHECKPOINT"

# exec prepared statement
#   arguments = (prepared_name_string, dyn=None)
#   execute the prepared statement with dynamic args.
#   autocommit.
EXECUTE_PREPARED = "EXECUTE_PREPARED"

# exec any statement (only if not disabled)
#   arguments = (statement_string, dyn=None)
#   execute the statement with dynamic args.
#   autocommit.
EXECUTE_STATEMENT = "EXECUTE_STATEMENT"

ACTIONS = [SHUTDOWN, RESTART, CHECKPOINT, 
           EXECUTE_PREPARED, EXECUTE_STATEMENT]
           
class Server:
    """database server: listen for commands"""
    
    verbose = 1
    
    # wait X minutes on each server loop
    select_timeout = 60*5
    
    # do a checkpoint each X times thru server loop
    check_loop = 5

    # for now works like finger/http
    #   == each command is a separate connection.
    # all sql commands constitute separate transactions
    #   which are automatically committed upon success.
    # for now commands come in as
    #  1 length (marshalled int)
    #  2 (password, data) (marshalled tuple)
    # responses come back as
    #  1 length (marshalled int)
    #  2 results (marshalled value)

    def __init__(self, port, db, dr, pw, startup=None):
        self.port = port
        self.db = db
        self.dr = dr
        self.pw = pw
        self.startup = startup
        self.connection = None
        self.socket = None
        # prepared cursors dictionary.
        self.cursors = {}
        self.policies = {}
        self.admin_policy = None

    def start(self):
        """after init, listen for commands."""
        from gfsocket import READY, ERROR, unpack_certified_data
        import sys
        verbose = self.verbose
        socket = self.socket
        connection = self.connection
        policies = self.policies
        admin_policy = self.admin_policy
        from select import select
        pending_connects = {}
        while 1:
            try:
                # main loop
                if self.check_loop<0: self.check_loop=5
                for i in xrange(self.check_loop):
                    if verbose:
                        print "main loop on", socket, connection
                    # checkpoint loop
                    sockets = [socket]
                    if pending_connects:
                        sockets = sockets + pending_connects.keys()
                    # wait for availability
                    if verbose:
                        print "server: waiting for connection(s)"
                    (readables, dummy, errors) = select(\
                       sockets, [], sockets[:], self.select_timeout)
                    if socket in errors:
                        raise ServerError, \
                          "listening socket in error state: aborting"
                    # clean up error connection sockets
                    for s in errors:
                        del pending_connects[s]
                        s.close()
                    # get a new connection, if available
                    if socket in readables:
                        readables.remove(socket)
                        (conn, addr) = socket.accept()
                        if 1 or verbose:
                            print "connect %s" % (addr,)
                        reader = Packet_Reader(conn)
                        pending_connects[conn] = reader
                    # poll readable pending connections, if possible
                    for conn in readables:
                        reader = pending_connects[conn]
                        mode = reader.mode
                        if not mode==READY:
                            if mode == ERROR:
                                # shouldn't happen
                                try:
                                    conn.close()
                                    del pending_connects[conn]
                                except: pass
                                continue
                            else:
                                try:
                                   reader.poll()
                                finally:
                                   pass # AFTER DEBUG CHANGE THIS!
                    # in blocking mode, service ready request, 
                    # commit on no error
                    for conn in pending_connects.keys():
                        reader = pending_connects[conn]
                        mode = reader.mode
                        if mode == ERROR:
                            try:
                                del pending_connects[conn]
                                conn.close()
                            except: pass
                        elif mode == READY:
                            try:
                                del pending_connects[conn]
                                data = reader.data
                                (actor_name, cert, md) = \
                                  unpack_certified_data(data)
                                # find the policy for this actor
                                if not policies.has_key(actor_name):
                                    if verbose:
                                        print "no such policy: "+actor_name
                                    reply_exception(NameError, 
                                     "no such policy: "+actor_name, conn)
                                    policy = None
                                else:
                                    if verbose:
                                        print "executing for", actor_name
                                    policy = policies[actor_name]
                                    policy.action(cert, md, conn)
                            except SHUTDOWN:
                                if policy is admin_policy:
                                    print \
  "shutdown on admin policy: terminating"
                                    connection.close()
                                    socket.close()
                                    # NORMAL TERMINATION:
                                    return
                            except RESTART:
                                if policy is admin_policy:
                                    print \
  "restart from admin policy: restarting connection"
                                    connection.restart()
                            except CHECKPOINT:
                                if policy is admin_policy:
                                    print \
  "checkpoint from admin policy: checkpointing now."
                                    connection.checkpoint()
                            except:
                                tb = sys.exc_traceback
                                info = "%s %s" % (sys.exc_type,
                                             str(sys.exc_value))
                                if verbose:
                                    from traceback import print_tb
                                    print_tb(tb)
                                print "error in executing action: "+info
                                reply_exception(
  ServerError, "exception: "+info, conn)
                        #break # stop after first request serviced!
            except:
                # except of main while 1 try statement
                tb = sys.exc_traceback
                ty = sys.exc_type
                va = sys.exc_value
                print "UNEXPECTED EXCEPTION ON MAINLOOP"
                from traceback import print_tb
                print_tb(tb)
                print "exception:", ty, va
            if not pending_connects:
                pending_connects = {}
            print "server: checkpointing"
            connection.checkpoint()

    def init(self):
        self.getconnection()
        self.startup_load()
        # get socket last in case of failure earlier
        self.getsocket()
        

    HOST = ""
    BACKLOG = 5
    
    def getsocket(self):
        """get the listening socket"""
        verbose = self.verbose
        import socket, sys
        if verbose:
            print "initializing listener socket"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if verbose:
                print "trying to set REUSEADDR",\
                       sock.getsockopt(socket.SOL_SOCKET,
                          socket.SO_REUSEADDR)
            sock.setsockopt(socket.SOL_SOCKET, 
                   socket.SO_REUSEADDR, 1)
        except: 
            if verbose: 
               print "set of REUSEADDR failed", sys.exc_type, sys.exc_value
            pass
        sock.bind(self.HOST, self.port)
        sock.listen(self.BACKLOG)
        self.socket = sock
        return sock
        
    def getconnection(self):
        """get the db connection"""
        from gadfly import gadfly
        c = self.connection = gadfly(self.db, self.dr)
        # don't automatically checkpoint upon commit
        c.autocheckpoint = 0

    def startup_load(self):
        """setup the policies and load startup module"""
        admin_policy = self.get_admin_policy()
        module_name = self.startup
        if module_name:
            module = __import__(module_name)
            # startup(admin_policy, connection, Server_instance)
            test = module.startup(admin_policy, self.connection, self)
            if test is not None:
                self.policies = test
        self.policies["admin"] = admin_policy
        
    def get_admin_policy(self):
        """return the admin policy for priviledged access."""
        p = self.admin_policy = Policy(
             "admin", self.pw, self.connection, queries=1)
        return p

class Policy:
    """security policy"""

    verbose = 0
    
    # allow arbitrary sql statments
    general_queries = 0
    
    # dictionary of named accesses as strings
    named_accesses = None
    
    # dictionary of prepared named accesses
    prepared_cursors = None
    
    def __init__(self, name, password, connection, queries=0):
        """create a policy (name, password, connection)
        
           name is the name of the policy
           password is the access policy (None for no password)
           connection is the database connection.
           set queries to allow general accesses (unrestricted)
        """
        if self.verbose:  
            print "policy.__init__", name
        self.general_queries = queries
        self.name = name
        self.password = password
        self.connection = connection
        self.socket = None
        self.named_accesses = {}
        self.prepared_cursors = {}
        
    def __setitem__(self, name, value):
        if self.verbose:
            print "policy", self.name, ":", (name, value)
        from types import StringType
        if type(name) is not StringType or type(value) is not StringType:
           raise ValueError, "cursor names and contents must be strings"
        self.named_accesses[name] = value
        
    def execute_named(self, name, params=None):
        """execute a named (prepared) sql statement"""
        if self.verbose:
            print "policy", self.name, "executes", name, params
        na = self.named_accesses
        pc = self.prepared_cursors
        con = self.connection
        if not na.has_key(name):
            raise PreparedNameError, "unknown access name: %s" % name
        stat = na[name]
        if pc.has_key(name):
            # get prepared query
            cursor = pc[name]
        else:
            # prepare a new cursor
            pc[name] = cursor = con.cursor()
        return self.execute(cursor, stat, params)
            
    def execute(self, cursor, statement, params=None):
        """execute a statement in a cursor"""
        if self.verbose:
            print "policy", self.name, "executes", statement, params
        cursor.execute(statement, params)
        # immediate commit!
        self.connection.commit()
        try:
            result = cursor.fetchall()
            description = cursor.description
            result = (description, result)
        except:
            result = None
        return result
        
    def execute_any_statement(self, statement, params=None):
        """execute any statement."""
        if self.verbose:
            print "policy", self.name, "executes", statement, params
        con = self.connection
        cursor = con.cursor()
        return self.execute(cursor, statement, params)
        
    def action(self, certificate, datastring, socket):
        """perform a database/server action after checking certificate"""
        verbose = self.verbose
        if verbose:
            print "policy", self.name, "action..."
        # make sure the certificate checks out
        if not self.certify(datastring, certificate, self.password):
            raise ServerError, "password certification failure"
        # unpack the datastring
        from marshal import loads
        test = loads(datastring)
        #if verbose:
            #print "data is", test
        (action, moredata) = test
        import sys
        if action in ACTIONS:
            action = "policy_"+action
            myaction = getattr(self, action)
            try:
                data = apply(myaction, moredata+(socket,))
                #self.reply_success(data)
            # pass up server level requests as exceptions
            except SHUTDOWN, detail:
                raise SHUTDOWN, detail
            except RESTART, detail:
                raise RESTART, detail
            except CHECKPOINT, detail:
                raise CHECKPOINT, detail
            except:
                tb = sys.exc_traceback
                exceptiondata = "%s\n%s" %(sys.exc_type,
                    str(sys.exc_value))
                if verbose:
                   from traceback import print_tb
                   print_tb(tb)
                self.reply_exception(ServerError, 
                  "unexpected exception: "+exceptiondata, socket)
                raise ServerError, exceptiondata
        else:
            raise ServerError, "unknown action: "+`action`
            
    def certify(self, datastring, certificate, password):
        # hook for subclassing
        return certify(datastring, certificate, password)
                
    def policy_SHUTDOWN(self, socket):
        self.reply_success("attempting server shutdown", socket)
        raise SHUTDOWN, "please shut down the server"
    
    def policy_RESTART(self, socket):
        self.reply_success("attempting server restart", socket)
        raise RESTART, "please restart the server"
        
    def policy_CHECKPOINT(self, socket):
        self.reply_success("attempting server checkpoint", socket)
        raise CHECKPOINT, "please checkpoint the server"
        
    def policy_EXECUTE_PREPARED(self, name, dyn, socket):
        try:
            result = self.execute_named(name, dyn)
            self.reply_success(result, socket)
        except PreparedNameError, detail:
            self.reply_exception(PreparedNameError, 
             "no such prepared statement: "+name,
             socket)
    
    def policy_EXECUTE_STATEMENT(self, stat, dyn, socket):
        if not self.general_queries:
            self.reply_exception(ServerError, 
               "general statements disallowed on this policy",
               socket)
            raise ServerError, "illegal statement attempt for: "+self.name
        result = self.execute_any_statement(stat, dyn)
        self.reply_success(result, socket)
        
    def reply_exception(self, exc, info, socket):
        # hook for subclassing
        reply_exception(exc, info, socket)
        
    def reply_success(self, data, socket):
        # hook for subclassing
        reply_success(data, socket)
        
if __name__=="__main__": main()
