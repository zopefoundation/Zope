# This external method will find all Page Template objects in the ZODB and
# attempt to parse them in order to find faulty templates. The result is
# returned as a list of errors.
#
# Create an object of type "External Method" at the root of your Zope site
# with module name "Products.PageTemplates.find_bad_templates" and function
# name "find_bad_templates". Execute is by visiting its "Test" tab
from zope.pagetemplate.pagetemplate import PTRuntimeError


RESULT_HTML = """\
<html>
  <head>
    <title>Find bad Page Templates</title>
  </head>
  <body>
    <h2>Page Template scan results</h2>
    <p>Found %(count)i bad out of %(total)i Page Template objects.</p>
    %(error_html)s
  </body>
</html>
"""

ERROR_HTML = """
<hr/>
<b>%(pt_path)s</b><br/>
<pre>
%(broken)s
</pre>
"""


def find_bad_templates(self):
    pt_errors = {}
    html_output = ''
    pts = self.ZopeFind(self,
                        obj_metatypes=('Page Template',
                                       'Filesystem Page Template'),
                        search_sub=True)

    for (pt_path, pt) in pts:
        if not pt_path.startswith('/'):
            pt_path = '/%s' % pt_path

        try:
            pt.pt_macros()
        except PTRuntimeError:
            # html quote "<" characters to be displayed as such
            pt_errors[pt_path] = [
                err.replace('<', '&lt;') for err in pt._v_errors]

    for pt_path in sorted(pt_errors.keys()):
        html_output += ERROR_HTML % {'pt_path': pt_path,
                                     'broken': '\n\n'.join(pt_errors[pt_path])}

    return RESULT_HTML % {'count': len(pt_errors),
                          'total': len(pts),
                          'error_html': html_output}
