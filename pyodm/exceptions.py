class OdmError(Exception):
    pass

class NodeServerError(OdmError):
    pass

class NodeConnectionError(OdmError):
    pass

class NodeResponseError(OdmError):
    pass