"""Public error hierarchy for all UPCP drivers."""


class UPCPError(Exception):
    """Base error for UPCP operations."""


class ConnectionError(UPCPError):
    """Connection or transport failed."""


class ProtocolError(UPCPError):
    """Received an invalid or unexpected protocol response."""


class DeviceError(UPCPError):
    """The remote device reported an error."""


class AddressError(UPCPError, ValueError):
    """Invalid or unsupported address."""


class WriteDisabledError(UPCPError):
    """Writes are disabled unless explicitly enabled."""
