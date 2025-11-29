"""Comprehensive logging utilities for the AI-Enhanced Interactive Book Agent.

This module provides structured logging configuration and utilities for all services
in the application, supporting different log levels, formats, and output destinations.
"""
import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import json
import traceback
from functools import wraps


class BookAgentLogger:
    """Centralized logging configuration for the book agent application."""

    def __init__(self):
        """Initialize the logger configuration."""
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self._setup_logging()

    def _setup_logging(self):
        """Set up the logging configuration."""
        # Create loggers for different components
        loggers_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'simple': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'json': {
                    'format': '%(asctime)s %(name)s %(levelname)s %(funcName)s %(lineno)d %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'simple',
                    'stream': sys.stdout
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'detailed',
                    'filename': self.log_dir / 'app.log',
                    'maxBytes': 10 * 1024 * 1024,  # 10 MB
                    'backupCount': 5
                },
                'error_file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'ERROR',
                    'formatter': 'detailed',
                    'filename': self.log_dir / 'error.log',
                    'maxBytes': 10 * 1024 * 1024,  # 10 MB
                    'backupCount': 5
                },
                'security_file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'INFO',
                    'formatter': 'detailed',
                    'filename': self.log_dir / 'security.log',
                    'maxBytes': 10 * 1024 * 1024,  # 10 MB
                    'backupCount': 5
                }
            },
            'loggers': {
                '': {  # Root logger
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False
                },
                'ai': {
                    'handlers': ['file'],
                    'level': 'DEBUG',
                    'propagate': False
                },
                'rag': {
                    'handlers': ['file'],
                    'level': 'DEBUG',
                    'propagate': False
                },
                'auth': {
                    'handlers': ['file', 'security_file'],
                    'level': 'INFO',
                    'propagate': False
                },
                'search': {
                    'handlers': ['file'],
                    'level': 'DEBUG',
                    'propagate': False
                },
                'database': {
                    'handlers': ['file'],
                    'level': 'INFO',
                    'propagate': False
                },
                'api': {
                    'handlers': ['file'],
                    'level': 'INFO',
                    'propagate': False
                }
            }
        }

        logging.config.dictConfig(loggers_config)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance with the specified name.

        Args:
            name: Name of the logger (typically module or class name)

        Returns:
            Logger instance
        """
        return logging.getLogger(name)

    def log_exception(self, logger: logging.Logger, message: str = "An exception occurred"):
        """Log an exception with traceback information.

        Args:
            logger: Logger instance to use
            message: Custom message to include with the exception
        """
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_type:
            logger.error(
                f"{message}: {exc_type.__name__}: {exc_value}",
                extra={
                    'exception_type': exc_type.__name__,
                    'exception_message': str(exc_value),
                    'traceback': traceback.format_tb(exc_traceback)
                }
            )

    def log_performance(
        self,
        logger: logging.Logger,
        operation: str,
        duration: float,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log performance metrics for operations.

        Args:
            logger: Logger instance to use
            operation: Name of the operation being logged
            duration: Duration of the operation in seconds
            details: Additional details about the operation
        """
        if details is None:
            details = {}

        level = logging.WARNING if duration > 1.0 else logging.INFO  # Log slow operations as warnings
        logger.log(
            level,
            f"Performance: {operation} took {duration:.3f}s",
            extra={
                'operation': operation,
                'duration_seconds': duration,
                'details': details
            }
        )

    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log security-related events.

        Args:
            event_type: Type of security event (e.g., 'login_attempt', 'permission_denied')
            user_id: ID of the user involved in the event
            ip_address: IP address of the request
            details: Additional details about the event
        """
        security_logger = self.get_logger('auth')
        security_logger.info(
            f"Security Event: {event_type}",
            extra={
                'event_type': event_type,
                'user_id': user_id,
                'ip_address': ip_address,
                'details': details or {}
            }
        )

    def log_ai_interaction(
        self,
        user_id: str,
        query: str,
        response: str,
        model_used: str,
        tokens_used: int = 0,
        processing_time: float = 0.0
    ):
        """Log AI interactions for monitoring and analytics.

        Args:
            user_id: ID of the user making the request
            query: The user's query
            response: The AI's response
            model_used: Name of the AI model used
            tokens_used: Number of tokens used in the interaction
            processing_time: Time taken to process the interaction
        """
        ai_logger = self.get_logger('ai')
        ai_logger.info(
            f"AI Interaction: User {user_id} queried '{query[:50]}...' and received response",
            extra={
                'user_id': user_id,
                'query': query,
                'response': response,
                'model_used': model_used,
                'tokens_used': tokens_used,
                'processing_time': processing_time
            }
        )

    def log_rag_operation(
        self,
        operation_type: str,
        query: str,
        results_count: int,
        processing_time: float,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log RAG (Retrieval-Augmented Generation) operations.

        Args:
            operation_type: Type of RAG operation (e.g., 'search', 'retrieve', 'generate')
            query: The search/query string
            results_count: Number of results returned
            processing_time: Time taken for the operation
            details: Additional details about the operation
        """
        rag_logger = self.get_logger('rag')
        rag_logger.info(
            f"RAG Operation: {operation_type} for query '{query[:50]}...' returned {results_count} results",
            extra={
                'operation_type': operation_type,
                'query': query,
                'results_count': results_count,
                'processing_time': processing_time,
                'details': details or {}
            }
        )


def log_function_call(logger: logging.Logger):
    """Decorator to log function calls with their arguments and results.

    Args:
        logger: Logger instance to use for logging
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__
            start_time = datetime.now()
            
            logger.debug(
                f"Calling function: {func_name}",
                extra={
                    'function_name': func_name,
                    'args': [str(arg)[:100] for arg in args],  # Limit arg length
                    'kwargs': {k: str(v)[:100] for k, v in kwargs.items()}  # Limit value length
                }
            )

            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.debug(
                    f"Function {func_name} completed successfully in {duration:.3f}s",
                    extra={
                        'function_name': func_name,
                        'duration': duration,
                        'result_type': type(result).__name__
                    }
                )
                
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(
                    f"Function {func_name} failed after {duration:.3f}s: {str(e)}",
                    extra={
                        'function_name': func_name,
                        'duration': duration,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__name__
            start_time = datetime.now()
            
            logger.debug(
                f"Calling function: {func_name}",
                extra={
                    'function_name': func_name,
                    'args': [str(arg)[:100] for arg in args],  # Limit arg length
                    'kwargs': {k: str(v)[:100] for k, v in kwargs.items()}  # Limit value length
                }
            )

            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.debug(
                    f"Function {func_name} completed successfully in {duration:.3f}s",
                    extra={
                        'function_name': func_name,
                        'duration': duration,
                        'result_type': type(result).__name__
                    }
                )
                
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(
                    f"Function {func_name} failed after {duration:.3f}s: {str(e)}",
                    extra={
                        'function_name': func_name,
                        'duration': duration,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
                raise

        # Return the appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_api_call(logger: logging.Logger):
    """Decorator to log API endpoint calls with request/response details.

    Args:
        logger: Logger instance to use for logging
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__
            start_time = datetime.now()
            
            # Extract request information if available
            request = None
            for arg in args:
                if hasattr(arg, 'client') and hasattr(arg, 'method'):
                    request = arg
                    break
            
            client_info = f"{request.client.host}:{request.client.port}" if request else "unknown"
            method = request.method if request else "unknown"
            
            logger.info(
                f"API Call: {method} {func_name}",
                extra={
                    'function_name': func_name,
                    'client_info': client_info,
                    'method': method,
                    'start_time': start_time.isoformat()
                }
            )

            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.info(
                    f"API Call {func_name} completed in {duration:.3f}s",
                    extra={
                        'function_name': func_name,
                        'duration': duration,
                        'result_type': type(result).__name__
                    }
                )
                
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(
                    f"API Call {func_name} failed after {duration:.3f}s: {str(e)}",
                    extra={
                        'function_name': func_name,
                        'duration': duration,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
                raise

        return async_wrapper

    return decorator


# Global instance of the logger manager
logger_manager = BookAgentLogger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.

    Args:
        name: Name of the logger (typically module or class name)

    Returns:
        Logger instance
    """
    return logger_manager.get_logger(name)


def init_logging():
    """Initialize the logging system."""
    # This function can be called at the start of the application
    # to ensure logging is properly set up
    pass  # The logger_manager is already initialized


# Convenience functions for common logging scenarios
def log_ai_interaction(user_id: str, query: str, response: str, model_used: str):
    """Log an AI interaction."""
    logger_manager.log_ai_interaction(user_id, query, response, model_used)


def log_rag_operation(operation_type: str, query: str, results_count: int, processing_time: float):
    """Log a RAG operation."""
    logger_manager.log_rag_operation(operation_type, query, results_count, processing_time)


def log_security_event(event_type: str, user_id: Optional[str] = None, ip_address: Optional[str] = None):
    """Log a security event."""
    logger_manager.log_security_event(event_type, user_id, ip_address)