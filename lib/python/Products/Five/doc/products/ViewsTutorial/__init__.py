import democontent

def initialize(context):

    context.registerClass(
        democontent.DemoContent,
        constructors = (democontent.manage_addDemoContentForm,
                        democontent.manage_addDemoContent),
        )
