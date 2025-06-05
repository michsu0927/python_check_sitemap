"""
Logging utilities for the Website Analyzer system.
Provides structured logging with different handlers and formatters.
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import traceback


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
            
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for console output."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format the message
        formatted = super().format(record)
        
        # Add color
        return f"{color}{formatted}{reset}"


class AnalysisLogger:
    """Enhanced logger for website analysis operations."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the analysis logger.
        
        Args:
            name: Logger name
            config: Logging configuration
        """
        self.logger = logging.getLogger(name)
        self.config = config or {}
        self._setup_logger()
        
    def _setup_logger(self):
        """Setup logger with handlers and formatters."""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set level
        level = self.config.get('level', 'INFO').upper()
        self.logger.setLevel(getattr(logging, level))
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        log_file = self.config.get('file_path', 'logs/analyzer.log')
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # JSON file handler for structured logs
        json_file = log_file.replace('.log', '_structured.json')
        json_handler = logging.handlers.RotatingFileHandler(
            json_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        json_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(json_handler)
        
    def analysis_start(self, url: str, analysis_id: str):
        """Log analysis start."""
        self.logger.info(
            f"Starting analysis for {url}",
            extra={'extra_data': {
                'event': 'analysis_start',
                'url': url,
                'analysis_id': analysis_id
            }}
        )
        
    def analysis_complete(self, url: str, analysis_id: str, duration: float, pages_count: int):
        """Log analysis completion."""
        self.logger.info(
            f"Analysis completed for {url} in {duration:.2f}s ({pages_count} pages)",
            extra={'extra_data': {
                'event': 'analysis_complete',
                'url': url,
                'analysis_id': analysis_id,
                'duration': duration,
                'pages_count': pages_count
            }}
        )
        
    def page_processed(self, url: str, page_url: str, processing_time: float):
        """Log page processing."""
        self.logger.debug(
            f"Processed page {page_url} in {processing_time:.2f}s",
            extra={'extra_data': {
                'event': 'page_processed',
                'website_url': url,
                'page_url': page_url,
                'processing_time': processing_time
            }}
        )
        
    def api_request(self, service: str, model: str, tokens_used: Optional[int] = None):
        """Log API requests."""
        message = f"API request to {service} ({model})"
        if tokens_used:
            message += f" - {tokens_used} tokens"
            
        self.logger.debug(
            message,
            extra={'extra_data': {
                'event': 'api_request',
                'service': service,
                'model': model,
                'tokens_used': tokens_used
            }}
        )
        
    def error_occurred(self, error: Exception, context: Dict[str, Any]):
        """Log errors with context."""
        self.logger.error(
            f"Error occurred: {str(error)}",
            exc_info=True,
            extra={'extra_data': {
                'event': 'error',
                'error_type': type(error).__name__,
                'context': context
            }}
        )
        
    def performance_metric(self, metric_name: str, value: float, unit: str = 'seconds'):
        """Log performance metrics."""
        self.logger.info(
            f"Performance metric: {metric_name} = {value:.3f} {unit}",
            extra={'extra_data': {
                'event': 'performance_metric',
                'metric_name': metric_name,
                'value': value,
                'unit': unit
            }}
        )
        
    def rate_limit_hit(self, service: str, retry_after: float):
        """Log rate limiting."""
        self.logger.warning(
            f"Rate limit hit for {service}, retrying after {retry_after}s",
            extra={'extra_data': {
                'event': 'rate_limit',
                'service': service,
                'retry_after': retry_after
            }}
        )
        
    def cache_hit(self, cache_key: str):
        """Log cache hits."""
        self.logger.debug(
            f"Cache hit: {cache_key}",
            extra={'extra_data': {
                'event': 'cache_hit',
                'cache_key': cache_key
            }}
        )
        
    def cache_miss(self, cache_key: str):
        """Log cache misses."""
        self.logger.debug(
            f"Cache miss: {cache_key}",
            extra={'extra_data': {
                'event': 'cache_miss',
                'cache_key': cache_key
            }}
        )


def get_logger(name: str, config: Optional[Dict[str, Any]] = None) -> AnalysisLogger:
    """
    Get an enhanced logger instance.
    
    Args:
        name: Logger name
        config: Logging configuration
        
    Returns:
        AnalysisLogger instance
    """
    return AnalysisLogger(name, config)


def setup_root_logger(config: Dict[str, Any]):
    """
    Setup root logger configuration.
    
    Args:
        config: Logging configuration
    """
    # Disable some noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Setup root logger
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        get_logger('root', config)
