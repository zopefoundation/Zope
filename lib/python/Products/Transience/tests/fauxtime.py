import time as origtime

epoch = origtime.time()

def time():
    """ False timer -- returns time 10 x faster than normal time """
    return (origtime.time() - epoch) * 10.0

def sleep(duration):
    """ False sleep -- sleep for 1/10 the time specifed """
    origtime.sleep(duration / 10.0)

