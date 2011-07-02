"""SiteAccess product
"""
def initialize(context):
    import SiteRoot
    import AccessRule
    import VirtualHostMonster

    context.registerClass(instance_class=SiteRoot.SiteRoot,
      permission='Add Site Roots',
      constructors=SiteRoot.constructors, legacy=SiteRoot.constructors)

    context.registerClass(instance_class=AccessRule.AccessRule,
      permission='Manage Access Rules', constructors=AccessRule.constructors)

    context.registerClass(instance_class=VirtualHostMonster.VirtualHostMonster,
      permission='Add Virtual Host Monsters',
      constructors=VirtualHostMonster.constructors)
