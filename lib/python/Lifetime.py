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

def setup_windows_control_handler():
    try:
        from win32api import SetConsoleCtrlHandler, \
                             GenerateConsoleCtrlEvent
        from win32con import CTRL_C_EVENT, CTRL_BREAK_EVENT, \
                             CTRL_CLOSE_EVENT, CTRL_LOGOFF_EVENT, \
                             CTRL_SHUTDOWN_EVENT
    except ImportError:
        pass
    else:
        def interrupt_select():
            """Interrupt a sleeping acyncore 'select' call"""
            # What is the right thing to do here?  
            # asyncore.close_all() works, but I fear that would
            # prevent the poll based graceful cleanup code from working.
            # This seems to work :)
            for fd, obj in asyncore.socket_map.items():
                if hasattr(obj, "pull_trigger"):
                    obj.pull_trigger()

        def ctrl_handler(ctrlType):
            """Called by Windows on a new thread whenever a
               console control event is raised."""
            result = 0
            if ctrlType == CTRL_C_EVENT:
                # user pressed Ctrl+C or someone did 
                # GenerateConsoleCtrlEvent
                if _shutdown_phase == 0:
                    print "Shutting down Zope..."
                    shutdown(0)
                    interrupt_select()
                elif _shutdown_timeout > 1.0:
                    print "Zope shutdown switching to 'fast'"
                    shutdown(0, 1)
                else:
                    # Third time around - terminate via
                    # a CTRL_BREAK_EVENT
                    GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, 0)
                result = 1
            elif ctrlType == CTRL_BREAK_EVENT:
                # Always let Ctrl+Break force it down.
                # Default handler terminates process.
                print "Terminating Zope (press Ctrl+C to shutdown cleanly)"
            elif ctrlType == CTRL_CLOSE_EVENT:
                # Console is about to die.
                # CTRL_CLOSE_EVENT gives us 5 seconds before displaying
                # the "End process" dialog - so switch directly to 'fast'
                shutdown(0, 1)
                interrupt_select()
                result = 1
            elif ctrlType in (CTRL_LOGOFF_EVENT, CTRL_SHUTDOWN_EVENT):
                # MSDN says:
                # "Note that this signal is received only by services. 
                # Interactive applications are terminated at logoff, so 
                # they are not present when the system sends this signal."
                # We can therefore ignore it (our service framework 
                # manages shutdown in this case)
                pass
            return result
        # Install our handler.
        SetConsoleCtrlHandler(ctrl_handler)
    
def loop():
    # Run the main loop until someone calls shutdown()
    lifetime_loop()
    # Gradually close sockets in the right order, while running a select
    # loop to allow remaining requests to trickle away.
    graceful_shutdown_loop()

def lifetime_loop():
    if sys.platform.startswith("win"):
        setup_windows_control_handler()

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
    
