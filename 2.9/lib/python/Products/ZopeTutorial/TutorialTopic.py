##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import OFS.Folder
from HelpSys.HelpTopic import TextTopic
from Globals import HTML, DTMLFile, MessageDialog
from cgi import escape
import DateTime
import DocumentTemplate
import StructuredText
import  re


pre_pat=re.compile(r'<PRE>(.+?)</PRE>', re.IGNORECASE|re.DOTALL)
tutorialExamplesFile='ZopeTutorialExamples.zexp'

class TutorialTopic(TextTopic):
    """
    A Tutorial Help Topic
    """

    def __init__(self, id, title, text):
        self.id=id
        self.title=title
        text=str(StructuredText.HTML(text))
        self.obj=HTML(pre_pat.sub(clean_pre, text))

    index_html=DTMLFile('dtml/lessonView', globals())

    def checkInstallation(self, REQUEST):
        """
        Returns false if the tutorial examples are not correctly
        installed. Also sets the 'hide_next' variable in the request
        if the examples are not installed.
        """
        ok=0
        if REQUEST.has_key('tutorialExamplesURL'):
            url=REQUEST['tutorialExamplesURL']
            base=REQUEST['BASE1']
            if url.index(base) == 0:
                url=url[len(base):]
                try:
                    self.getPhysicalRoot().unrestrictedTraverse(url)
                    ok=1
                except:
                    pass

        if not ok:
            REQUEST.set('hide_next', 1)
        return ok

    def lessonURL(self, id, REQUEST):
        """
        URL of the examples for a lesson
        """
        try:
            return '%s/lesson%d' % (REQUEST['tutorialExamplesURL'], id)
        except KeyError:
            return ""

    def tutorialShowLesson(self, id, REQUEST):
        """
        Navigate management frame to a given lesson's screen.
        """
        url=self.lessonURL(id, REQUEST)
        if not url or not self.checkInstallation(REQUEST):
            REQUEST.set('hide_next', 0)
            return """\
<p class="warning">
Zope cannot find the tutorial examples.
You should install the tutorial examples before
continuing. Choose "Zope Tutorial" from the product
add list in the Zope management screen to install
the examples.
</p>
<p class="warning">
If you have already installed the tutorial, you can either
follow along manually, or reinstall the tutorial examples.
Note: make sure that you have cookies turned on in your browser.
</p>
"""

        return """\
<SCRIPT LANGUAGE="javascript">
<!--
window.open("%s/manage_main", "manage_main");
//-->
</SCRIPT>
<p class="information">
<a href="%s/manage_main" target="manage_main"
onClick="javascript:window.open('%s/manage_main', 'manage_main').focus()"
>Show lesson examples</a> in another window.
</p>""" % (url.replace('"', '\\"'), escape(url, 1),
           escape(url, 1).replace("'", "\\'"))


    tutorialNavigation=DTMLFile('dtml/tutorialNav', globals())


class GlossaryTopic(TutorialTopic):
    """
    A Tutorial Glossary Help Topic
    """

    def __init__(self, id, title, text):
        self.id=id
        self.title=title
        self.obj=HTML(text)

    index_html=DTMLFile('dtml/glossaryView', globals())

    def formatted_content(self, REQUEST):
        """
        Custom stx formatting for tutorial topics
        """
        text=self.obj(self, REQUEST)
        text=str(StructuredText.HTML(text))
        pre_pat.sub(clean_pre, text)
        return text

    def apiLink(self, klass, REQUEST):
        """
        Returns the URL to a API documentation for a given class.
        """
        names=klass.split('.')
        url="%s/Control_Panel/Products/%s/Help/%s.py#%s" % (REQUEST['SCRIPT_NAME'],
                names[0], names[1], names[2])
        return '<a href="%s">API Documentation</a>' % url

    def dtmlLink(self, tag, REQUEST):
        """
        Returns the URL to a DTML Reference page for a given tag.
        """
        url="%s/Control_Panel/Products/OFSP/Help/dtml-%s.stx" % (REQUEST['SCRIPT_NAME'], tag)
        return '<a href="%s">DTML Reference</a>' % url

    def zptLink(self, tag, REQUEST):
        """
        Returns the URL to a ZPT Reference page for a given topic.
        """
        url="%s/Control_Panel/Products/PageTemplates/Help/%s.stx" % (REQUEST['SCRIPT_NAME'], tag)
        return '<a href="%s">ZPT Reference</a>' % url



addTutorialForm=DTMLFile('dtml/tutorialAdd', globals())

def addTutorial(self, id, REQUEST=None, RESPONSE=None):
    """
    Install tutorial examples.
    """
    id=str(id)
    ob=OFS.Folder.Folder()
    ob.id=id
    ob.title='Zope Tutorial Examples'
    id=self._setObject(id, ob)
    folder=getattr(self, id)

    # make sure that Gadfly is initialized
    try:
        from Products.ZGadflyDA.DA import data_sources
        data_sources()
    except:
        raise 'Bad Request', 'The ZGadflyDA product must be installed!'

    # work around old Zope bug in importing
    try:
        folder.manage_importObject(tutorialExamplesFile)
    except:
        folder._p_jar=self.Destination()._p_jar
        folder.manage_importObject(tutorialExamplesFile)

    # acquire REQUEST if necessary
    if REQUEST is None:
        REQUEST=self.REQUEST

    # Set local roles on examples
    changeOwner(folder, REQUEST['AUTHENTICATED_USER'])

    # Run lesson setup methods -- call Setup.setup methods in lesson folders
    examples=folder.examples
    for lesson in examples.objectValues():
        if hasattr(lesson, 'Setup'):
            lesson.Setup.setup(lesson.Setup, REQUEST)

    if RESPONSE is not None:
        e=(DateTime.DateTime('GMT') + 365).rfc822()
        RESPONSE.setCookie('tutorialExamplesURL', folder.absolute_url() + '/examples',
                path='/',
                expires=e)
        RESPONSE.redirect(folder.absolute_url() + '/examples')


def changeOwner(obj, owner):
    """
    Recursively changes the Owner of an object and all its subobjects.
    """
    for user, roles in obj.get_local_roles():
        if 'Owner' in roles:
            obj.manage_delLocalRoles([user])
            break
    obj.manage_setLocalRoles(owner.getId(), ['Owner'])
    for subobj in obj.objectValues():
        changeOwner(subobj, owner)

def clean_pre(match):
    """
    Reformat a pre tag to get rid of extra indentation
    and extra blank lines.
    """
    lines=match.group(1).split('\n')
    nlines=[]

    min_indent=None
    for line in lines:
        indent=len(line) - len(line.lstrip())
        if min_indent is None or indent < min_indent:
            if line.strip():
                min_indent=indent
    for line in lines:
        nlines.append(line[min_indent:])

    while 1:
        if not nlines[0].strip():
            nlines.pop(0)
        else:
            break

    while 1:
        if not nlines[-1].strip():
            nlines.pop()
        else:
            break

    return "<PRE>%s</PRE>" % '\n'.join(nlines)
