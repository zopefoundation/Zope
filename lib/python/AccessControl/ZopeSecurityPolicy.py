#

from SimpleObjectPolicies import _noroles

if 0: # cAccessControl is not working
    import cAccessControl

    ZopeSecurityPolicy = cAccessControl.ZopeSecurityPolicy
else:
    from pZopeSecurityPolicy import ZopeSecurityPolicy
