import os, sys
DEBUG = 0
if os.name in ('posix', 'nt', 'dos'):
    EXCLUDED_NAMES=['..', '.']
else:
    EXCLUDED_NAMES=[]

# extend EXCLUDED_NAMES here manually with filenames ala "asyncore.pyc" for
# files that are only distributed in compiled format (.pyc, .pyo)
# if necessary (not currently necessary in 2.3.1 AFAIK) - chrism

def walkandscrub(path):
    path = os.path.expandvars(os.path.expanduser(path))
    print
    print '-'*78
    sys.stdout.write(
        "Deleting '.pyc' and '.pyo' files recursively under %s... " % path
        )
    os.path.walk(path, scrub, [])
    sys.stdout.write('done.\n')

def scrub(list, dirname, filelist):
    for name in filelist:
        if name in EXCLUDED_NAMES:
            continue
        prefix, ext = os.path.splitext(name)
        if ext == '.pyo' or ext == '.pyc':
            full = os.path.join(dirname, name)
            os.unlink(full)
            if DEBUG: print full
            
if __name__ == '__main__':
    DEBUG = 1
    walkandscrub(os.getcwd())
