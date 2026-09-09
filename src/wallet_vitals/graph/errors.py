class GraphError(RuntimeError):
    """Base class for safe, user-facing data provider failures."""


class GraphConfigurationError(GraphError):
    pass


class GraphTransportError(GraphError):
    pass


class GraphResponseError(GraphError):
    pass


class GraphStaleDataError(GraphError):
    pass


class GraphIndexingError(GraphError):
    pass
