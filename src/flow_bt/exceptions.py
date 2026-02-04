"""Custom exceptions for Flow BT."""

class FlowBTError(Exception):
    """Base exception for Flow BT."""
    pass

class ConnectionError(FlowBTError):
    """Raised when connection to the device fails."""
    pass

class AuthenticationError(FlowBTError):
    """Raised when authentication with the device fails."""
    pass

class NotConnectedError(FlowBTError):
    """Raised when an operation is attempted while disconnected."""
    pass

class ProtocolError(FlowBTError):
    """Raised when a protocol violation occurs."""
    pass
