"""Ledger-specific exceptions raised by repositories (converted to AppError in services)."""


class InsufficientBalanceError(Exception):
    def __init__(self, message: str = "Insufficient available balance") -> None:
        self.message = message
        super().__init__(message)


class InsufficientLockedError(Exception):
    def __init__(self, message: str = "Insufficient locked balance") -> None:
        self.message = message
        super().__init__(message)
