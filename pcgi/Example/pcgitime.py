# pcgitime.py - example pcgi script - JeffBauer@bigfoot.com

from time import asctime, localtime, time

beginTime = "<html><pre>time started: %s" % asctime(localtime(time()))

def getTime(arg=None):
    """It's later than you think (don't remove this docstring)"""
    return "%s\ncurrent time: %s" % (beginTime, asctime(localtime(time())))
