class OdmError(Exception):
    """Generic catch-all exception. All exceptions in pyodm inherit from it."""
    pass

class NodeServerError(OdmError):
    """The server replied in a manner which we did not expect. Usually this indicates
    a temporary malfunction of the node."""
    pass

class NodeConnectionError(OdmError):
    """A connection problem (such as a timeout or a network error) has occurred."""
    pass

class NodeResponseError(OdmError):
    """The node responded with an error message indicating that the requested operation failed."""
    pass

class TaskFailedError(OdmError):
    """A task did not complete successfully."""
    pass

class RangeNotAvailableError(OdmError):
    """A download attempt to use Range requests failed."""
    pass