##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import TutorialTopic
import App.Common
import os.path
import os
import stat
from DateTime import DateTime
from urllib import quote_plus
from cgi import escape
import re
from HelpSys import APIHelpTopic


def initialize(context):
    # abuse registerClass to get a tutorial constructor
    # in the product add list
    context.registerClass(
        None,
        meta_type='Zope Tutorial',
        constructors=(TutorialTopic.addTutorialForm, TutorialTopic.addTutorial),
        )

    from App.Product import doInstall

    if not doInstall():
        return

    # create tutorial help topics
    lesson_path=os.path.join(App.Common.package_home(globals()), 'tutorial.stx')
    glossary_path=os.path.join(App.Common.package_home(globals()), 'glossary.stx')
    help=context.getProductHelp()

    # test to see if nothing has changed since last registration
    if help.lastRegistered is not None and \
            help.lastRegistered >= DateTime(os.stat(lesson_path)[stat.ST_MTIME]):
        return
    help.lastRegistered=DateTime()

    # delete old help topics
    for id in help.objectIds('Help Topic'):
        help._delObject(id)

    # create glossary
    text=open(glossary_path).read()
    text=term_pat.sub(defineTerm, text)

    glossary=TutorialTopic.GlossaryTopic('tutorialGlossary',
                                         'Zope Tutorial Glossary', text)
    context.registerHelpTopic('tutorialGlossary', glossary)

    # create lessons
    f=open(lesson_path)
    lines=[]
    id=0

    while 1:
        line = f.readline()
        if (line.strip() and line.find(' ') != 0) or line=='':
            # new topic
            if lines:
                id = id + 1
                topic_id = 'topic_%02d' % id
                text=''.join(lines[1:])
                text=term_pat.sub(glossaryTerm, text)
                topic=TutorialTopic.TutorialTopic(topic_id, lines[0].strip(), spacestrip(text))
                context.registerHelpTopic(topic_id, topic)
            lines=[line]
        else:
            lines.append(line)
        if line == '':
            break
    f.close()


def spacestrip(txt):
    """ dedent text by 2 spaces !

    We need this to workaround a nasty bug in STXNG.
    STXNG creates empty <pre>..</pre> when then text start
    if a level > 1. This fix is lame. The problem should be fixed
    inside STXNG
    """

    l = []
    for x in txt.split("\n"):
        if len(x)>2 and x[:2]=='  ':
            l.append(x[2:])
        else: l.append(x)

    return '\n'.join(l)


# Glossary functions
# ----------------

term_pat=re.compile('\[(.*?)\]')
terms=[]

def glossaryTerm(match):
    """
    A linked glossary term
    """
    name=match.group(1)
    if name in terms:
        return """<a href="../tutorialGlossary#%s">%s</a>""" % \
                (quote_plus(name), escape(name))
    return """[%s]""" % name

def defineTerm(match):
    """
    Define a glossary term
    """
    name=match.group(1)
    terms.append(name)
    return """<a name="%s"></a>\n\n<strong>%s</strong>""" % \
            (quote_plus(name), escape(name))
