def set_read_multi():
    import re
    global valid_boundary
    valid_boundary = re.compile("^[ -~]{0,200}[!-~]$").match

    def read_multi(self, environ, keep_blank_values, strict_parsing):
        """Internal: read a part that is itself multipart."""
        ib = self.innerboundary
        if not valid_boundary(ib):
            raise ValueError, ('Invalid boundary in multipart form: %s' 
                               % `ib`)
        self.list = []
        klass = self.FieldStorageClass or self.__class__
        part = klass(self.fp, {}, ib,
                     environ, keep_blank_values, strict_parsing)
        # Throw first part away
        while not part.done:
            headers = rfc822.Message(self.fp)
            part = klass(self.fp, headers, ib,
                         environ, keep_blank_values, strict_parsing)
            self.list.append(part)
        self.skip_lines()
    FieldStorage.read_multi = read_multi

import cgi
exec set_read_multi.func_code in cgi.__dict__
