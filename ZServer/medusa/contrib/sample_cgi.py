# -*- Mode: Python; tab-width: 4 -*-

import time

def main (env, stdin, stdout):

        # write out the response
    stdout.write ("HTTP/1.0 200 OK\r\n")
    
    # write out a header
    stdout.write ("Content-Type: text/html\r\n")
    stdout.write ("\r\n")
    
    stdout.write ("<html><body>")
    for i in range (10,0,-1):
        stdout.write ("<br> <b>tick</b> %d\r\n" % i)
        stdout.flush()
        time.sleep (3)
        
    stdout.write ("</body></html>\r\n")
