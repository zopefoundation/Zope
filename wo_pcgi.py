"""Try to do all of the installation steps.

This must be run from the top-level directory of the installation.
(Yes, this is cheezy.  We'll fix this when we have a chance.

"""

import os
home=os.getcwd()
print
print '-'*78
print 'Compiling py files'
import compileall
compileall.compile_dir(os.getcwd())

import build_extensions

print
print '-'*78

os.chdir(home)
data_dir=os.path.join(home, 'var')
db_path=os.path.join(data_dir, 'Data.bbb')
dd_path=os.path.join(data_dir, 'Data.bbb.in')
if not os.path.exists(data_dir):
    print 'creating data directory'
    os.mkdir('var')
    
if not os.path.exists(db_path):
    print 'creating default database'
    os.system('cp %s %s' % (dd_path, db_path))

ac_path=os.path.join(home, 'access')
if not os.path.exists(ac_path):
    print 'creating default access file'
    acfile=open(ac_path, 'w')
    acfile.write('superuser:123\n')
    acfile.close()
    os.system('chmod 744 access')
    
print
print '-'*78
print 'NOTE: change owndership or permissions on var so that it can be'
print '      written by the web server!'
print
print "NOTE: The default super user name and password are 'superuser'"
print "      and '123'.  Create a file named 'access' in this directory"
print "      with a different super user name and password on one line"
print "      separated by a a colon. (e.g. 'spam:eggs').  You can also"
print "      specify a domain (e.g. 'spam:eggs:*.digicool.com')."
print '-'*78
print
print 'Done!'
