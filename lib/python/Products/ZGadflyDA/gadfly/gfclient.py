
"""client access to gadfly server. (gfserve.py)

Imported as a module this module provides interfaces
that remotely access a gadfly database server.

Remote connections: gfclient

   connection = gfclient.gfclient(
      policy,  # the name of the connection policy ["admin" for admin]
      port,    # the port number the server is running on
      password,# the password of the policy
      [machine]) # (optional) the machine where server is running
                 # (defaults to localhost)

   methods for gfclient connections:
      gfclient.checkpoint() checkpoint the server (fails silently
          if connection is not "admin").
      gfclient.restart() restart the server (fails silently
          if connection is not "admin").
      gfclient.shutdown() shutdown the server (fails silently
          if connection is not "admin").
      cursor = gfclient.cursor() returns a cursor on this connection

   methods for cursor objects:

      cursor.execute(statement, dynamic_parameters=None)
          execute the statement with optional dynamic parameters.
          Dynamic parameters can be a list of tuples for INSERT
          VALUES statements, otherwise they must be a tuple
          of values.
      cursor.execute_prepared(name, dynamic_parameters=None)
          execute a named statement configured for this connection
          policy, with optional dynamic parameters. Dynamic
          parameters permitted as for execute depending on the
          statement the name refers to.
      cursor.fetchall()
          return results of the last executed statement
          (None for non-queries, or list of tuples).

See gfstest.py for example usage.
     
SCRIPT INTERPRETATION:

Server maintenance utilities

COMMAND LINE:
   python gfclient.py action port admin_password [machine]

TEST EXAMPLE:
   python gfclient.py shutdown 2222 admin

   action: one of
      shutdown:  shut down the server with no checkpoint
      restart: restart the server (re-read the database and recover)
      checkpoint: force a database checkpoint now
   port: the port the server is running on
   admin_password: the administrative password for the server
   machine: [optional] the machine the server runs on.
"""

import gfsocket

def main():
    import sys
    try:
        done=0
        argv = sys.argv
        [action, port, admin_password] = argv[1:4]
        from string import atoi
        port = atoi(port)
        if len(argv)>4:
           machine = argv[4]
        else:
           machine = None
        print action, port, admin_password, machine
        if action not in ["shutdown", "restart", "checkpoint"]:
           print "bad action", action
           print
           return
        dosimple(action, port, admin_password, machine)
        done=1
    finally:
        if not done:
            print __doc__

def dosimple(action, port, pw, machine=None):
    import socket
    if machine is None:
       machine = socket.gethostname()
    conn = gfclient("admin", port, pw, machine)
    action = getattr(conn, action)
    print action()

# copied from gfserve
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

class gfclient:

    closed = 0
    
    def __init__(self, policy, port, password, machine=None):
        import socket
        self.policy = policy
        self.port = port
        self.password = password
        if machine is None:
            machine = socket.gethostname()
        self.machine = machine
        
    def open_connection(self):
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #print type(sock), sock
        sock.connect(self.machine, self.port)
        return sock
        
    def send_action(self, action, arguments, socket):
        gfsocket.send_certified_action(
          self.policy, action, arguments, self.password, socket)
        
    def checkpoint(self):
        return self.simple_action(CHECKPOINT)
    
    def simple_action(self, action, args=()):
        """only valid for admin policy: force a server checkpoint"""
        sock = self.open_connection()
        self.send_action(action, args, sock)
        data = gfsocket.recv_data(sock)
        data = gfsocket.interpret_response(data)
        return data
    
    def restart(self):
        """only valid for admin policy: force a server restart"""
        return self.simple_action(RESTART)
        
    def shutdown(self):
        """only valid for admin policy: shut down the server"""
        return self.simple_action(SHUTDOWN)
    
    def close(self):
        self.closed = 1
        
    def commit(self):
        # right now all actions autocommit
        pass
        
    # cannot rollback, autocommit on success
    rollback = commit
    
    def cursor(self):
        """return a cursor to this policy"""
        if self.closed:
            raise ValueError, "connection is closed"
        return gfClientCursor(self)
        

class gfClientCursor:

    statement = None
    results = None
    description = None

    def __init__(self, connection):
        self.connection = connection
        
    # should add fetchone fetchmany
    def fetchall(self):
        return self.results
    
    def execute(self, statement=None, params=None):
        con = self.connection
        data = con.simple_action(EXECUTE_STATEMENT, (statement, params))
        (self.description, self.results) = data
    
    def execute_prepared(self, name, params=None):
        con = self.connection
        data = con.simple_action(EXECUTE_PREPARED, (name, params))
        if data is None:
            self.description = self.results = None
        else:
            (self.description, self.results) = data
    
    def setoutputsizes(self, *args):
        pass # not implemented
        
    def setinputsizes(self):
        pass # not implemented
        
if __name__=="__main__":
    main()
