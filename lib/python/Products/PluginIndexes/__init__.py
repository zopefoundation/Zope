import common.PluggableIndex as PluggableIndex
import common.ResultList     as ResultList
import common.UnIndex        as UnIndex

from Globals import DTMLFile

import PathIndex.PathIndex 
import TextIndex.TextIndex 
import FieldIndex.FieldIndex
import KeywordIndex.KeywordIndex

def initialize(context):

    context.registerClass(
        PathIndex.PathIndex.PathIndex,
        permission='Add Pluggable Index',
        constructors=(manage_addPathIndexForm,
                      manage_addPathIndex),
        icon="www/index.gif",
        visibility=None
    )

    context.registerClass(
        TextIndex.TextIndex.TextIndex,
        permission='Add Pluggable Index',
        constructors=(manage_addTextIndexForm,
                      manage_addTextIndex),
        icon="www/index.gif",
        visibility=None
    )

    context.registerClass(
        FieldIndex.FieldIndex.FieldIndex,
        permission='Add Pluggable Index',
        constructors=(manage_addFieldIndexForm,
                      manage_addFieldIndex),
        icon="www/index.gif",
        visibility=None
    )


    context.registerClass(
        KeywordIndex.KeywordIndex.KeywordIndex,
        permission='Add Pluggable Index',
        constructors=(manage_addKeywordIndexForm,
                      manage_addKeywordIndex),
        icon="www/index.gif",
        visibility=None
    )


    context.registerHelp()
    context.registerHelpTitle('Indexes (Pluggable)')

manage_addTextIndexForm = TextIndex.TextIndex.manage_addTextIndexForm
manage_addTextIndex     = TextIndex.TextIndex.manage_addTextIndex

manage_addPathIndexForm = PathIndex.PathIndex.manage_addPathIndexForm
manage_addPathIndex     = PathIndex.PathIndex.manage_addPathIndex

manage_addFieldIndexForm = FieldIndex.FieldIndex.manage_addFieldIndexForm
manage_addFieldIndex     = FieldIndex.FieldIndex.manage_addFieldIndex

manage_addKeywordIndexForm = KeywordIndex.KeywordIndex.manage_addKeywordIndexForm
manage_addKeywordIndex     = KeywordIndex.KeywordIndex.manage_addKeywordIndex



