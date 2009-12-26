from zope.deferredimport import deprecated

deprecated("Please import from five.formlib",
    ObjectWidgetView = 'five.formlib.objectwidget:ObjectWidgetView',
    ObjectWidget = 'five.formlib.objectwidget:ObjectWidget',
    ObjectWidgetClass = 'five.formlib.objectwidget:ObjectWidgetClass',
)
