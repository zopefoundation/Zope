__doc__="""SiteAccess product"""

import SiteRoot, AccessRule, VirtualHostMonster

def initialize(context):
    context.registerClass(instance_class=SiteRoot.SiteRoot,
      permission='Add Site Roots',
      constructors=SiteRoot.constructors, legacy=SiteRoot.constructors,
      icon='www/SiteRoot.gif')
    context.registerClass(instance_class=AccessRule.AccessRule,
      permission='Manage Access Rules', constructors=AccessRule.constructors,
      icon='www/AccessRule.gif')
    context.registerClass(instance_class=VirtualHostMonster.VirtualHostMonster,
      permission='Add Virtual Host Monsters',
      constructors=VirtualHostMonster.constructors,
      icon='www/VirtualHostMonster.gif')
    context.registerHelp()
