print
print '-'*78
print 'Compiling py files'
import compileall, os
compileall.compile_dir(os.getcwd())
