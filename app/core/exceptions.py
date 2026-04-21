class AppError(Exception):
    pass


class CarreraNotFound(AppError):
    pass


class PerfilNotFound(AppError):
    pass


class ETLError(AppError):
    pass


class SSRFBlockedError(AppError):
    pass


class IntegrityCheckError(AppError):
    pass


class SessionExpiredError(AppError):
    pass
