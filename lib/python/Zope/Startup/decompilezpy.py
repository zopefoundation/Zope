import os
import sys

def main(dirname):
    os.path.walk(dirname, rmpycs, None)

def rmpycs(arg, dirname, names):
    for name in names:
        path = os.path.join(dirname, name)
        if ( name.endswith('.pyc') or name.endswith('.pyo') and
             os.path.isfile(path) ):
            os.unlink(path)

if __name__ == '__main__':
    main(sys.argv[1])
