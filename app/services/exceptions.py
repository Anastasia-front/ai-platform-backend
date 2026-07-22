class ApplicationError(Exception):
    status_code = 400


class InvalidProviderConfigurationError(ApplicationError):
    status_code = 400


class AuthenticationFailedError(ApplicationError):
    status_code = 401


class ResourceNotFoundError(ApplicationError):
    status_code = 404


class ResourceConflictError(ApplicationError):
    status_code = 409
