##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
import OFS.Folder
from HelpSys.HelpTopic import TextTopic
from Globals import HTML, HTMLFile, MessageDialog
import DateTime
import DocumentTemplate
import StructuredText
import string, re


pre_pat=re.compile(r'<PRE>(.+?)</PRE>', re.DOTALL)
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
        
    index_html=HTMLFile('lessonView', globals())
            
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
        if not url:
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
onClick="javascript:window.open("%s/manage_main", "manage_main").focus()"
>Show lesson examples</a> in another window.
</p>""" % (url, url, url)

    def apiLink(self, klass, REQUEST):
        """
        Returns the URL to a API documentation for a given class.
        """
        names=string.split(klass, '.')
        url="%s/Control_Panel/Products/%s/Help/%s.py#%s" % (REQUEST['SCRIPT_NAME'],
                names[0], names[1], names[2])
        return '<a href="%s">API Documentation</a>' % url

    tutorialNavigation=HTMLFile('tutorialNav', globals())


addTutorialForm=HTMLFile('tutorialAdd', globals())

def addTutorial(self, id, REQUEST=None, RESPONSE=None):
    """
    Install tutorial examples.
    """
    ob=OFS.Folder.Folder()
    ob.id=id
    ob.title='Zope Tutorial Examples'
    id=self._setObject(id, ob)
    folder=getattr(self, id)

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
    obj.manage_setLocalRoles(owner.getUserName(), ['Owner'])
    for subobj in obj.objectValues():
        changeOwner(subobj, owner)
        
def clean_pre(match):
    """
    Reformat a pre tag to get rid of extra indentation
    and extra blank lines.
    """
    lines=string.split(match.group(1), '\n')
    nlines=[]

    min_indent=None
    for line in lines:
        indent=len(line) - len(string.lstrip(line))
        if min_indent is None or indent < min_indent:
            if string.strip(line):
                min_indent=indent   
    for line in lines:
        nlines.append(line[min_indent:])
    
    while 1:
        if not string.strip(nlines[0]):
            nlines.pop(0)
        else:
            break
    
    while 1:
        if not string.strip(nlines[-1]):
            nlines.pop()
        else:
            break
    
    return "<PRE>%s</PRE>" % string.join(nlines, '\n')
