__doc__="""SiteAccess product"""

import SiteRoot, AccessRule, VirtualHostMonster

def initialize(context):
  context.registerClass(instance_class=SiteRoot.SiteRoot, 
    constructors=SiteRoot.constructors, legacy=SiteRoot.constructors,
    icon='www/SiteRoot.gif')
  context.registerClass(instance_class=AccessRule.AccessRule,
    permission='Set Access Rule', constructors=AccessRule.constructors,
    icon='www/AccessRule.gif')
  context.registerClass(instance_class=VirtualHostMonster.VirtualHostMonster,
    permission='Create Virtual Host Monster',
    constructors=VirtualHostMonster.constructors,
    icon='www/VirtualHostMonster.gif')
  context.registerHelp()
