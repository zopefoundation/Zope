import os
import shutil

def create_lib_python(options, buildout):
    if os.path.exists(options['dst-dir']):
        shutil.rmtree(options['dst-dir'])
    shutil.copytree(options['src-dir'], options['dst-dir'])
    for pathname in options['skip-names'].split():
        path = os.path.join(options['dst-dir'], pathname)
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
