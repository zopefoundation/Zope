##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

def initialize(context):

    from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
    from Products.PluginIndexes.FieldIndex.FieldIndex \
        import manage_addFieldIndex
    from Products.PluginIndexes.FieldIndex.FieldIndex \
        import manage_addFieldIndexForm
    context.registerClass(FieldIndex,
                          permission='Add Pluggable Index', 
                          constructors=(manage_addFieldIndexForm,
                                        manage_addFieldIndex),
                          icon='www/index.gif',
                          visibility=None,
                         )

    from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex
    from Products.PluginIndexes.KeywordIndex.KeywordIndex \
        import manage_addKeywordIndex
    from Products.PluginIndexes.KeywordIndex.KeywordIndex \
        import manage_addKeywordIndexForm
    context.registerClass(KeywordIndex,
                          permission='Add Pluggable Index', 
                          constructors=(manage_addKeywordIndexForm,
                                        manage_addKeywordIndex),
                          icon='www/index.gif',
                          visibility=None,
                         )

    from Products.PluginIndexes.TopicIndex.TopicIndex import TopicIndex
    from Products.PluginIndexes.TopicIndex.TopicIndex \
        import manage_addTopicIndex
    from Products.PluginIndexes.TopicIndex.TopicIndex \
        import manage_addTopicIndexForm
    context.registerClass(TopicIndex,
                          permission='Add Pluggable Index', 
                          constructors=(manage_addTopicIndexForm,
                                        manage_addTopicIndex),
                          icon='www/index.gif',
                          visibility=None,
                         )

    from Products.PluginIndexes.DateIndex.DateIndex import DateIndex
    from Products.PluginIndexes.DateIndex.DateIndex \
        import manage_addDateIndex
    from Products.PluginIndexes.DateIndex.DateIndex \
        import manage_addDateIndexForm
    context.registerClass(DateIndex,
                          permission='Add Pluggable Index', 
                          constructors=(manage_addDateIndexForm,
                                        manage_addDateIndex),
                          icon='www/index.gif',
                          visibility=None,
                         )

    from Products.PluginIndexes.DateRangeIndex.DateRangeIndex \
        import DateRangeIndex
    from Products.PluginIndexes.DateRangeIndex.DateRangeIndex \
        import manage_addDateRangeIndex
    from Products.PluginIndexes.DateRangeIndex.DateRangeIndex \
        import manage_addDateRangeIndexForm
    context.registerClass(DateRangeIndex,
                          permission='Add Pluggable Index', 
                          constructors=(manage_addDateRangeIndexForm,
                                        manage_addDateRangeIndex),
                          icon='www/index.gif',
                          visibility=None,
                         )

    from Products.PluginIndexes.PathIndex.PathIndex import PathIndex
    from Products.PluginIndexes.PathIndex.PathIndex \
        import manage_addPathIndex
    from Products.PluginIndexes.PathIndex.PathIndex \
        import manage_addPathIndexForm
    context.registerClass(PathIndex,
                          permission='Add Pluggable Index', 
                          constructors=(manage_addPathIndexForm,
                                        manage_addPathIndex),
                          icon='www/index.gif',
                          visibility=None,
                         )
