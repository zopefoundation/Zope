def initialize(context):
    from Products.SiteAccess import VirtualHostMonster

    context.registerClass(
        instance_class=VirtualHostMonster.VirtualHostMonster,
        permission='Add Virtual Host Monsters',
        constructors=VirtualHostMonster.constructors,
    )
