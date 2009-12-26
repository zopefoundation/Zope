from zope.deferredimport import deprecated

deprecated("Please import from five.formlib.formbase",
    FiveFormlibMixin = 'five.formlib.formbase:FiveFormlibMixin',
    FormBase = 'five.formlib.formbase:FormBase',
    EditFormBase = 'five.formlib.formbase:EditFormBase',
    DisplayFormBase = 'five.formlib.formbase:DisplayFormBase',
    AddFormBase = 'five.formlib.formbase:AddFormBase',
    PageForm = 'five.formlib.formbase:PageForm',
    PageEditForm = 'five.formlib.formbase:PageEditForm',
    EditForm = 'five.formlib.formbase:EditForm',
    PageDisplayForm = 'five.formlib.formbase:PageDisplayForm',
    DisplayForm = 'five.formlib.formbase:DisplayForm',
    PageAddForm = 'five.formlib.formbase:PageAddForm',
    AddForm = 'five.formlib.formbase:AddForm',
    SubPageForm = 'five.formlib.formbase:SubPageForm',
    SubPageEditForm = 'five.formlib.formbase:SubPageEditForm',
    SubPageDisplayForm = 'five.formlib.formbase:SubPageDisplayForm',
)
