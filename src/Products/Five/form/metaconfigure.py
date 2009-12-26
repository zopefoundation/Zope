from zope.deferredimport import deprecated

deprecated("Please import from five.formlib",
    EditViewFactory = 'five.formlib.metaconfigure:EditViewFactory',
    FiveFormDirective = 'five.formlib.metaconfigure:FiveFormDirective',
    EditFormDirective = 'five.formlib.metaconfigure:EditFormDirective',
    AddViewFactory = 'five.formlib.metaconfigure:AddViewFactory',
    AddFormDirective = 'five.formlib.metaconfigure:AddFormDirective',
)
