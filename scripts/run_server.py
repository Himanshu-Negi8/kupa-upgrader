#!/usr/bin/env python3
"""
Script to run the KuPa server with proper logging configuration.
"""

import os
import logging
import argparse
import uvicorn

def main():
    """Run the KuPa server."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run KuPa server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--log-level", default="info", 
                        choices=["debug", "info", "warning", "error", "critical"],
                        help="Log level")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    # Set up logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr"
            }
        },
        "loggers": {
            "kupa": {"handlers": ["default"], "level": args.log_level.upper()},
            "uvicorn": {"handlers": ["default"], "level": "INFO"}
        }
    }
    
    # Run the server
    print(f"Starting KuPa server on {args.host}:{args.port}...")
    uvicorn.run(
        "kupa.api.server:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload,
        log_config=logging_config
    )
    
if __name__ == "__main__":
    main()
