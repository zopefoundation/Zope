import sys
import time as origtime

epoch = origtime.time()

resolution = 120.0
timeout = 30

if sys.platform[:3].lower() == "win":
    resolution = 60.0
    timeout = 60


def time():
    """ False timer -- returns time R x faster than normal time """
    return (origtime.time() - epoch) * resolution

def sleep(duration):
    """ False sleep -- sleep for 1/R the time specifed """
    origtime.sleep(duration / resolution)
