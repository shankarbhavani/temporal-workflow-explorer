#!/usr/bin/env python3
"""
Temporal Worker Startup Script

This script starts the Temporal worker that processes workflow and activity tasks.
Make sure Temporal server is running at the configured host before starting the worker.

Usage:
    python run_worker.py
"""
import asyncio
from app.temporal.worker import run_worker


def main():
    """
    Start the Temporal worker.
    """
    print("=" * 60)
    print("Starting Temporal Worker")
    print("=" * 60)
    print()

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print("\n\nWorker stopped by user.")
    except Exception as e:
        print(f"\n\nError running worker: {e}")
        raise


if __name__ == "__main__":
    main()
