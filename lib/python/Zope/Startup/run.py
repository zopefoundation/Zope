
# this function will actually start up a Zope instance
def run():
    import App.config
    from Zope.Startup import handlers, options, start_zope

    opts = options.ZopeOptions()
    opts.realize()
    handlers.handleConfig(opts.configroot, opts.confighandlers)
    App.config.setConfiguration(opts.configroot)
    start_zope(opts.configroot)

if __name__ == '__main__':
    run()

