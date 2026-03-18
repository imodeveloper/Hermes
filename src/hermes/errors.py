"""Hermes-specific exceptions."""


class HermesError(Exception):
    """Base Hermes error."""


class ConfigError(HermesError):
    """Raised when configuration is invalid or missing."""


class CommandError(HermesError):
    """Raised when a subprocess command fails."""

    def __init__(self, message: str, *, command: str, exit_code: int, stderr: str = "") -> None:
        super().__init__(message)
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr


class LockError(HermesError):
    """Raised when a lock cannot be acquired."""

