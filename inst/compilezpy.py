print
print '-'*78
print 'Compiling py files'
import compileall
compileall.compile_dir(os.getcwd())
