#!/usr/bin/env python
"""Load a Zope site from a collection of files or directories
"""

usage=""" [options] url file .....

    where options are:

      -p path

         Path to ZPublisher

      -u user:password

         Credentials

      -v

         Run in verbose mode.

"""

import sys, getopt, os, string
ServerError=''
verbose=0

def main():
    user, password = 'superuser', '123'
    opts, args = getopt.getopt(sys.argv[1:], 'p:u:v')
    global verbose
    for o, v in opts:
        if o=='-p':
            d, f = os.path.split(v)
            if f=='ZPublisher': sys.path.insert(0,d)
            else: sys.path.insert(0,v)
        elif o=='-u':
            v = string.split(v,':')
            user, password = v[0], string.join(v[1:],':')
        elif o=='-v': verbose=1

    if not args:
        print sys.argv[0]+usage
        sys.exit(1)

    url=args[0]
    files=args[1:]

    import ZPublisher.Client
    global ServerError
    ServerError=ZPublisher.Client.ServerError
    object=ZPublisher.Client.Object(url, username=user, password=password)

    for f in files: upload_file(object, f)

def call(f, *args, **kw):
    # Call a function ignoring redirect bci errors.
    try: apply(f,args, kw)
    except ServerError, v:
        if str(v)[:1] != '3':
            raise sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]

def upload_file(object, f):
    if os.path.isdir(f): return upload_dir(object, f)
    dir, name = os.path.split(f)
    root, ext = os.path.splitext(name)
    if ext in ('file', 'dir'): ext=''
    else:
        ext=string.lower(ext)
        if ext and ext[0] in '.': ext=ext[1:]
    if ext and globals().has_key('upload_'+ext):
        if verbose: print 'upload_'+ext, f
        return globals()['upload_'+ext](object, f)

    if verbose: print 'upload_file', f, ext
    call(object.manage_addFile, id=name, file=open(f))

def upload_dir(object, f):
    if verbose: print 'upload_dir', f
    dir, name = os.path.split(f)
    call(object.manage_addFolder, id=name)
    object=object.__class__(object.url+'/'+name,
                            username=object.username,
                            password=object.password)
    for n in os.listdir(f):
        upload_file(object, os.path.join(f,n))

def upload_html(object, f):
    dir, name = os.path.split(f)
    f=open(f)
    # There is a Document bugs that causes file uploads to fail.
    # Waaa.  This will be fixed in 1.10.2.
    f=f.read()
    call(object.manage_addDTMLDocument, id=name, file=f)
    
upload_htm=upload_html

def upload_dtml(object, f):
    dir, name = os.path.split(f)
    call(object.manage_addDTMLMethod, id=name, file=open(f))
        

def upload_gif(object, f):
    dir, name = os.path.split(f)
    call(object.manage_addImage, id=name, file=open(f))

upload_jpg=upload_gif
upload_png=upload_gif

if __name__=='__main__': main()


