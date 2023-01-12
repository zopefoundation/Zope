import html
import io
import re
import unittest

from Products.PageTemplates.ZopePageTemplate import manage_addPageTemplate
from Testing.utils import capture_stdout
from Testing.ZopeTestCase import ZopeTestCase

from .util import useChameleonEngine


macro_outer = """
<metal:defm define-macro="master">
    <metal:defs define-slot="main_slot">
      Outer Slot
    </metal:defs>
</metal:defm>
""".strip()

macro_middle = """
<metal:def define-macro="master">
  <metal:use use-macro="here/macro_outer/macros/master">
    <metal:fill fill-slot="main_slot">
      <metal:defs define-slot="main_slot">
        Middle Slot
      </metal:defs>
    </metal:fill>
  </metal:use>
</metal:def>
""".strip()

macro_inner = """
<metal:use use-macro="here/macro_middle/macros/master">
  <metal:fills fill-slot="main_slot">
    <tal:block i18n:domain="mydomain" i18n:translate="">
      Inner Slot
    </tal:block>
  </metal:fills>
</metal:use>
""".strip()

simple_i18n = """
<tal:block i18n:domain="mydomain" i18n:translate="">
  Hello, World
</tal:block>
""".strip()

simple_error = """
<tal:block content__typo="nothing">
  it's an error to use an unknown attribute in the tal namespace
</tal:block>
""".strip()

repeat_object = """
<tal:loop repeat="counter python: range(3)"
          content="python: repeat['counter'].index" />
""".strip()

options_capture_update_base = """
<metal:use use-macro="context/macro_outer/macros/master">
  <metal:fills fill-slot="main_slot">
    <tal:block define="dummy python: capture.update(%s)" />
  </metal:fills>
</metal:use>
""".strip()

lp_848200_source = """
<tal:block>
  <tag tal:condition="python:False"
       tal:attributes="attrib string:false" />
  <tag tal:condition="python:True"
       tal:attributes="attrib string:true" />
</tal:block>
""".strip()

tal_onerror_structure_source = """
<tal:block tal:on-error="structure python: '&lt;i&gt;error!&lt;/i&gt;'">
  <i tal:content="python: 1/0" />
</tal:block>
""".strip()

python_nbsp_source = """
<p tal:content="structure python: '&amp;nbsp;'" />
""".strip()

python_path_source = """
<form tal:attributes="method python:path('context/method')" />
""".strip()


def generate_capture_source(names):
    params = ", ".join(f"{name}={name}"
                       for name in names)
    return options_capture_update_base % (params,)


textarea_content_search = re.compile(
    r'<textarea[^>]*>([^<]+)</textarea>',
    re.IGNORECASE | re.MULTILINE
).search


def get_editable_content(template):
    edit_form = template.pt_editForm()
    editable_text = textarea_content_search(edit_form).group(1)
    return editable_text


_marker = object()


class TestPersistent(ZopeTestCase):

    def afterSetUp(self):
        useChameleonEngine()
        self.setRoles(['Manager'])

    def _makeOne(self, template_id, source):
        return manage_addPageTemplate(self.folder, template_id, text=source)

    def test_simple(self):
        template = self._makeOne('foo', simple_i18n)
        result = template().strip()
        self.assertEqual(result, 'Hello, World')
        editable_text = get_editable_content(template)
        self.assertEqual(editable_text, html.escape(simple_i18n, False))

    def test_escape_on_edit(self):
        # check that escapable chars can round-trip intact.
        source = "&gt; &amp; &lt;"
        template = self._makeOne('foo', source)
        self.assertEqual(template(), source)  # nothing to render
        editable_text = get_editable_content(template)
        self.assertEqual(editable_text, html.escape(source, False))

    def test_macro_with_i18n(self):
        self._makeOne('macro_outer', macro_outer)
        self._makeOne('macro_middle', macro_middle)
        inner = self._makeOne('macro_inner', macro_inner)
        result = inner().strip()
        self.assertEqual(result, 'Inner Slot')

    def test_pt_render_with_macro(self):
        # The pt_render method of ZopePageTemplates allows rendering the
        # template with an expanded (and overriden) set of context
        # variables.
        # Lets test with some common and some unique variables:
        extra_context = dict(form=object(),
                             context=self.folder,
                             here=object(),)
        capture = {name: None for name in extra_context}
        source = generate_capture_source(capture)
        self._makeOne('macro_outer', macro_outer)
        template = self._makeOne('test_pt_render', source)
        extra_context['capture'] = capture
        template.pt_render(extra_context=extra_context)
        del extra_context['capture']
        self.assertEqual(extra_context, capture)
        # pt_render is also used to retrieve the unrendered source for
        # TTW editing purposes.
        self.assertEqual(template.pt_render(source=True), source)

    def test_avoid_recompilation(self):
        template = self._makeOne('foo', simple_i18n)

        # Template is already cooked
        program = template._v_program
        template.pt_render({})

        # The program does not change
        self.assertEqual(program, template._v_program)

    def test_repeat_object_security(self):
        template = self._makeOne('foo', repeat_object)
        # this should not raise an Unauthorized error
        self.assertEqual(template().strip(), '012')
        # The rest of this test is not actually testing
        # the security access, but I couldn't find a simpler
        # way to test if the RepeatItem instance itself allows public
        # access, and there are convoluted situations in production
        # that need RepeatItem to be declared public.
        src = """
          <tal:b repeat="x python: range(1)">
             <tal:b define="dummy python: options['do'](repeat)" />
          </tal:b>
        """.strip()

        def do(repeat):
            subobject_access = '__allow_access_to_unprotected_subobjects__'
            self.assertTrue(getattr(repeat['x'], subobject_access, False))

        template = self._makeOne('bar', src)
        template(do=do)

    def test_path_function(self):
        # check that the "path" function inside a python expression works
        self.folder.method = 'post'
        template = self._makeOne('foo', python_path_source)
        self.assertEqual(template(), '<form method="post" />')

    def test_filename_attribute(self):
        # check that a persistent page template that happens to have
        # a filename attribute doesn't break
        template = self._makeOne('foo', repeat_object)
        template.filename = 'some/random/path'
        # this should still work, without trying to open some random
        # file on the filesystem
        self.assertEqual(template().strip(), '012')

    def test_edit_with_errors(self):
        # Prevent error output to the console
        with capture_stdout(io.StringIO()):
            template = self._makeOne('foo', simple_error)

        # this should not raise:
        editable_text = get_editable_content(template)
        # and the errors should be in an xml comment at the start of
        # the editable text
        error_prefix = html.escape(
            '<!-- Page Template Diagnostics\n {}\n-->\n'.format(
                '\n '.join(template._v_errors)
            ),
            False,
        )
        self.assertTrue(editable_text.startswith(error_prefix))

    def test_lp_848200(self):
        # https://bugs.launchpad.net/chameleon.zpt/+bug/848200
        template = self._makeOne('foo', lp_848200_source)
        self.assertEqual(template().strip(), '<tag attrib="true" />')

    def test_onerror_structure(self):
        template = self._makeOne('foo', tal_onerror_structure_source)
        self.assertEqual(template().strip(), '<i>error!</i>')

    def test_python_nbsp(self):
        template = self._makeOne('foo', python_nbsp_source)
        self.assertEqual(template().strip(), '<p>&nbsp;</p>')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestPersistent)
