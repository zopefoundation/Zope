import sys, asyncore, time

_shutdown_phase = 0
_shutdown_timeout = 30 # seconds per phase

# The shutdown phase counts up from 0 to 4.
#
# 0  Not yet terminating. running in main loop
#
# 1  Loss of service is imminent. Prepare any front-end proxies for this
#    happening by stopping any ICP servers, so that they can choose to send
#    requests to other Zope servers in the cluster.
#
# 2  Stop accepting any new requests.
#
# 3  Wait for all old requests to have been processed
#
# 4  Already terminated
#
# It is up to individual socket handlers to implement these actions, by
# providing the 'clean_shutdown_control' method. This is called intermittantly
# during shutdown with two parameters; the current phase number, and the amount
# of time that it has currently been in that phase. This method should return
# true if it does not yet want shutdown to proceed to the next phase.

def shutdown(exit_code,fast = 0):
    global _shutdown_phase
    global _shutdown_timeout
    if _shutdown_phase == 0:
        # Thread safety? proably no need to care
        import ZServer
        ZServer.exit_code = exit_code
        _shutdown_phase = 1
    if fast:
        # Someone wants us to shutdown fast. This is hooked into SIGTERM - so
        # possibly the system is going down and we can expect a SIGKILL within
        # a few seconds.  Limit each shutdown phase to one second. This is fast
        # enough, but still clean.
        _shutdown_timeout = 1.0

def loop():
    # Run the main loop until someone calls shutdown()
    lifetime_loop()
    # Gradually close sockets in the right order, while running a select
    # loop to allow remaining requests to trickle away.
    graceful_shutdown_loop()

def lifetime_loop():
    # The main loop. Stay in here until we need to shutdown
    map = asyncore.socket_map
    timeout = 30.0
    while map and _shutdown_phase == 0:
        asyncore.poll(timeout, map)

        
def graceful_shutdown_loop():
    # The shutdown loop. Allow various services to shutdown gradually.
    global _shutdown_phase
    timestamp = time.time()
    timeout = 1.0
    map = asyncore.socket_map
    while map and _shutdown_phase < 4:
        time_in_this_phase = time.time()-timestamp 
        veto = 0
        for fd,obj in map.items():
            try:
                fn = getattr(obj,'clean_shutdown_control')
            except AttributeError:
                pass
            else:
                try:
                    veto = veto or fn(_shutdown_phase,time_in_this_phase)
                except:
                    obj.handle_error()
        if veto and time_in_this_phase<_shutdown_timeout:
            # Any open socket handler can veto moving on to the next shutdown
            # phase.  (but not forever)
            asyncore.poll(timeout, map)
        else:
            # No vetos? That is one step closer to shutting down
            _shutdown_phase += 1
            timestamp = time.time()
    
