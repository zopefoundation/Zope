# -*- Mode: Python; tab-width: 4 -*-

import asyncore
import http_server
import script_handler
import filesys

h = http_server.http_server ('', 8081)
fs = filesys.os_filesystem ('.')
sh = script_handler.script_handler (fs)

import persistent
ph = script_handler.persistent_script_handler()
ph.add_module ('per', persistent)

# install the two handlers
# Hit me as: http://www.your_server.com:8081/per
h.install_handler (ph)
# Hit me as: http://www.your_server.com:8081/form.mpy
h.install_handler (sh)

asyncore.loop()
