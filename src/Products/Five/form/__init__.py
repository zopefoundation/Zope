from zope.deferredimport import deprecated

deprecated("Please import from five.formlib",
    AddView = 'five.formlib:AddView',
    EditView = 'five.formlib:EditView',
)
