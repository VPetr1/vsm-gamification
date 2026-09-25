class ScenarioError(Exception):
    """Domain error with a stable machine-readable code; the API maps codes to HTTP statuses."""

    def __init__(self, code: str, message: str, **extra):
        super().__init__(message)
        self.code = code
        self.message = message
        self.extra = extra
