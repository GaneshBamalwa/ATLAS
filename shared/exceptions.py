"""
shared/exceptions.py - Centralized Custom Exception Classes
"""

class ATLASException(Exception):
    """Base exception for all ATLAS microservices"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# LLM / Reasoning Exceptions
class LLMError(ATLASException):
    """Raised when an inference call fails"""
    pass

class LLMTimeoutError(LLMError):
    """Raised when an LLM provider request times out"""
    pass

class LLMAuthenticationError(LLMError):
    """Raised when authorization with an LLM provider fails"""
    pass


# Tool Exceptions
class ToolError(ATLASException):
    """Base exception for tool executions"""
    pass

class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not registered"""
    pass

class ToolExecutionError(ToolError):
    """Raised when executing a tool raises an unhandled exception"""
    pass

class ToolTimeoutError(ToolError):
    """Raised when tool execution exceeds limits"""
    pass


# Auth / Connection Exceptions
class AuthenticationError(ATLASException):
    """Raised when user credentials or tokens are invalid/expired"""
    pass

class ServiceConnectionError(ATLASException):
    """Raised when communicating with another microservice fails"""
    pass
