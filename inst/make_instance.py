##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""Make an INSTANCE_HOME."""

import sys, os, string

def setup(me):
    home=os.path.abspath(os.path.split(me)[0])
    return os.path.split(home)[0]

def get_ih(home):
    print 'The instance home is the directory from which you will run Zope.'
    print 'Several instance homes, each with their own data and'
    print 'configuration, can share one copy of Zope.'
    while 1:
        print
        ih = raw_input('Instance home [%s]: ' % home)
        if ih == '': ih = home
        else: ih = os.path.abspath(ih)
        if not os.path.exists(ih):
            print '%s does not exist.' % `ih`
            make_ih = raw_input('Shall I create it [y]? ')
            if make_ih and make_ih[0] not in 'yY': continue
            try:
                os.mkdir(ih, 0775)
            except:
                print 'Unable to create %s' % `ih`
            else:
                print 'Created.'
                return ih
        elif not os.path.isdir(ih):
            print '%s is not a directory.' % `ih`
        else:
            print "%s exists, so I left it alone." % `ih`
            return ih

def main(me):
    home=setup(me)
    ih = get_ih(home)

    # Make skeleton
    for dirname in ('Extensions', 'import', 'Products', 'var'):
        mode = (dirname == 'var') and 0711 or 0775
        dirpath = os.path.join(ih, dirname)
        if not os.path.isdir(dirpath):
            os.mkdir(dirpath, mode)
            print 'Created %s directory.' % `dirname`

    # Set up Data.fs
    db_path = os.path.join(ih, 'var', 'Data.fs')
    dd_path = os.path.join(home, 'var', 'Data.fs.in')
    if os.path.exists(db_path):
        print 'Database exists, so I left it alone.'
    elif os.path.exists(dd_path):
        open(db_path,'wb').write(open(dd_path,'rb').read())
        print 'Created default database'

    # Set up other *.in files
    # Note: They will be %-substituted, so quote '%'s!
    idata = {'python': sys.executable, 'software_home': home}
    from glob import glob
    for infile in glob(os.path.join(home, 'inst', '*.in')):
        fn = os.path.split(infile)[1][:-3]
        target = os.path.join(ih, fn)
        if os.path.exists(target):
            print '%s exists, so I left it alone' % fn
        else:
            txt = open(infile, 'rb').read() % idata
            outfile = open(target, 'wb')
            outfile.write(txt)
            outfile.close()
            os.chmod(target, 0700)
            print 'Created %s' % fn

    print '-'*78
    print
    print ('Now to create a starting user. Leave the username '
           'blank if you want to skip this step.')
    print 
    sys.path.insert(0, home)
    choose_inituser(ih)

def choose_inituser(home):
    ac_path=os.path.join(home, 'inituser')
    if not os.path.exists(ac_path):
        import getpass, zpasswd
        print '-'*78
        print 'Please choose a username and password.'
        print 'This will create the initial user with which you manage Zope.'
        username = raw_input("Username: ")
        if username == '':
            return
               
        while 1:
            pw = getpass.getpass("Password: ")
            verify = getpass.getpass("Verify password: ")
            if verify == pw:
                break
            else:
                pw = verify = ''
                print "Password mismatch, please try again..."
        acfile=open(ac_path, 'w')
        acfile.write('%s:%s' % (username, zpasswd.generate_passwd(pw, 'SHA')))
        acfile.close()

        import do; do.ch(ac_path, '', '', mode=0644)

if __name__=='__main__': main(sys.argv[0])
