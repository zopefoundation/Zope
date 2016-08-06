

def initialize(context):
    import VirtualHostMonster

    context.registerClass(
        instance_class=VirtualHostMonster.VirtualHostMonster,
        permission='Add Virtual Host Monsters',
        constructors=VirtualHostMonster.constructors,
    )
