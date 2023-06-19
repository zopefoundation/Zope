import sys


def f1():
    return sys._getframe(0).f_code.co_filename
