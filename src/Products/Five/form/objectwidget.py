from zope.deferredimport import deprecated

deprecated("Please import from five.formlib.objectwidget",
    ObjectWidgetView = 'five.formlib.objectwidget:ObjectWidgetView',
    ObjectWidget = 'five.formlib.objectwidget:ObjectWidget',
    ObjectWidgetClass = 'five.formlib.objectwidget:ObjectWidgetClass',
)
